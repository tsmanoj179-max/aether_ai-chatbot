import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentSearchRequest,
    DocumentSearchResult,
    CollectionSummary
)
from backend.app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Document Intelligence & RAG"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    db: Session = Depends(get_db)
):
    """
    Validates file extension, size, stores in uploads directory,
    and runs background extraction, chunking, and vector indexing.
    """
    orig_name = file.filename or "uploaded_file"
    ext = os.path.splitext(orig_name)[1].lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Secure random filename on disk
    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}_{orig_name}"
    dest_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    # Stream write with size check
    total_size = 0
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    with open(dest_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 64)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_bytes:
                buffer.close()
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                )
            buffer.write(chunk)

    doc = Document(
        id=file_id,
        collection_name=collection.strip() or "default",
        filename=orig_name,
        file_type=ext,
        file_size=total_size,
        file_path=dest_path,
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Trigger indexing immediately
    document_service.process_and_index_document(db, doc.id)
    db.refresh(doc)

    return DocumentResponse.model_validate(doc)

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    collection: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if collection:
        query = query.filter(Document.collection_name == collection)
    return [DocumentResponse.model_validate(d) for d in query.order_by(Document.created_at.desc()).all()]

@router.get("/collections", response_model=List[CollectionSummary])
def list_collections(db: Session = Depends(get_db)):
    docs = db.query(Document).all()
    collections: dict[str, dict] = {}
    for d in docs:
        col = d.collection_name
        if col not in collections:
            collections[col] = {"name": col, "document_count": 0, "total_chunks": 0}
        collections[col]["document_count"] += 1
        collections[col]["total_chunks"] += d.chunk_count

    return [CollectionSummary(**v) for v in collections.values()]

@router.post("/search", response_model=List[DocumentSearchResult])
def search_documents(
    payload: DocumentSearchRequest,
    db: Session = Depends(get_db)
):
    """Retrieves top-k relevant chunks across the collection using sparse vector cosine similarity."""
    return document_service.search_collection(
        db,
        query=payload.query,
        collection_name=payload.collection_name,
        top_k=payload.top_k
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "id": document_id}
