import os
import re
import math
import logging
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from pypdf import PdfReader
from docx import Document as DocxDocument
from backend.app.config import settings
from backend.app.models.document import Document, DocumentChunk
from backend.app.schemas.document import DocumentSearchResult

logger = logging.getLogger("aetherai.rag")

class DocumentService:
    @staticmethod
    def extract_text_from_file(file_path: str, file_ext: str) -> List[Tuple[int, str]]:
        """
        Extracts text from file.
        Returns list of (page_or_section_number, text_content).
        """
        ext = file_ext.lower()
        pages: List[Tuple[int, str]] = []

        if ext == ".pdf":
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    pages.append((i + 1, txt))

        elif ext == ".docx":
            doc = DocxDocument(file_path)
            full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            pages.append((1, full_text))

        elif ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                pages.append((1, content))

        elif ext in [".xlsx"]:
            try:
                import csv
                # Simple fallback read if converted or plain
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    pages.append((1, content))
            except Exception:
                pages.append((1, "Spreadsheet uploaded."))

        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
            try:
                from backend.app.services.image_service import image_service
                with open(file_path, "rb") as f:
                    ibytes = f.read()
                props = image_service.analyze_image_properties(ibytes)
                colors = ", ".join(props.get("dominant_colors", []))
                desc = (
                    f"--- Image Document: {os.path.basename(file_path)} ---\n"
                    f"Type: Image ({props.get('format', 'IMAGE')})\n"
                    f"Resolution: {props.get('width', 0)}x{props.get('height', 0)} ({props.get('aspect_ratio', '1:1')})\n"
                    f"Megapixels: {props.get('megapixels', 0)} MP | Brightness: {int(props.get('brightness', 0.5) * 100)}%\n"
                    f"Color Palette: {colors}\n"
                )
                pages.append((1, desc))
            except Exception:
                pages.append((1, f"Image document: {os.path.basename(file_path)}"))

        return pages

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
        """Sliding window chunking with word boundary awareness."""
        words = text.split()
        if not words:
            return []

        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunks.append(" ".join(chunk_words))
            if i + chunk_size >= len(words):
                break
            i += max(1, chunk_size - overlap)
        return chunks

    @staticmethod
    def compute_bow_vector(text: str) -> Dict[str, float]:
        """Computes normalized term frequency vector for lightweight, CPU-efficient cosine retrieval."""
        tokens = re.findall(r'\b[a-zA-Z0-9_]{3,}\b', text.lower())
        if not tokens:
            return {}
        counts = Counter(tokens)
        total = sum(counts.values())
        norm = math.sqrt(sum((c / total) ** 2 for c in counts.values()))
        if norm == 0:
            return {}
        return {term: (count / total) / norm for term, count in counts.items()}

    @staticmethod
    def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculates cosine similarity between two sparse unit vectors."""
        if not vec1 or not vec2:
            return 0.0
        # Iterate over smaller vector for performance
        if len(vec1) > len(vec2):
            vec1, vec2 = vec2, vec1
        return sum(val * vec2.get(term, 0.0) for term, val in vec1.items())

    def process_and_index_document(self, db: Session, doc_id: str) -> int:
        """Extracts text, chunks, computes vectors, and persists to database."""
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return 0

        try:
            document.status = "processing"
            db.commit()

            pages = self.extract_text_from_file(document.file_path, document.file_type)
            chunk_index = 0
            created_chunks = []

            for page_num, text in pages:
                text_chunks = self.chunk_text(
                    text,
                    chunk_size=settings.RAG_CHUNK_SIZE,
                    overlap=settings.RAG_CHUNK_OVERLAP
                )
                for chunk_str in text_chunks:
                    if len(chunk_str.strip()) < 10:
                        continue
                    bow = self.compute_bow_vector(chunk_str)
                    chunk_obj = DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        page_number=page_num,
                        content=chunk_str,
                        token_count=len(chunk_str.split()),
                        embedding=bow,
                        metadata_json={
                            "filename": document.filename,
                            "collection": document.collection_name,
                            "page": page_num
                        }
                    )
                    created_chunks.append(chunk_obj)
                    chunk_index += 1

            db.add_all(created_chunks)
            document.chunk_count = chunk_index
            document.status = "ready"
            db.commit()
            return chunk_index

        except Exception as e:
            logger.error(f"Failed to process document {doc_id}: {e}")
            document.status = "error"
            document.error_message = str(e)
            db.commit()
            return 0

    def search_collection(
        self,
        db: Session,
        query: str,
        collection_name: Optional[str] = None,
        top_k: int = 4
    ) -> List[DocumentSearchResult]:
        """
        Retrieves top-k relevant chunks across the collection using sparse vector cosine similarity.
        """
        query_vec = self.compute_bow_vector(query)
        if not query_vec:
            return []

        # Query eligible document chunks
        db_query = db.query(DocumentChunk).join(Document)
        if collection_name:
            db_query = db_query.filter(Document.collection_name == collection_name)
        db_query = db_query.filter(Document.status == "ready")

        all_chunks = db_query.all()
        scored_chunks: List[Tuple[float, DocumentChunk]] = []

        for chunk in all_chunks:
            embedding = chunk.embedding or {}
            score = self.cosine_similarity(query_vec, embedding)
            if score >= settings.RAG_SIMILARITY_THRESHOLD:
                scored_chunks.append((score, chunk))

        # Sort descending by similarity
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results: List[DocumentSearchResult] = []
        for score, chunk in scored_chunks[:top_k]:
            results.append(
                DocumentSearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    filename=chunk.document.filename,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    similarity_score=round(score, 4),
                    metadata=chunk.metadata_json
                )
            )

        return results

document_service = DocumentService()
