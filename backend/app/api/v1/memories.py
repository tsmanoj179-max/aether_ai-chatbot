from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse
)
from backend.app.services.memory_service import memory_service

router = APIRouter(prefix="/memories", tags=["Long-Term Memory"])

@router.get("", response_model=List[MemoryResponse])
def get_memories(
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    memories = memory_service.list_memories(db, active_only=active_only)
    return [MemoryResponse.model_validate(m) for m in memories]

@router.post("", response_model=MemoryResponse)
def add_memory(
    payload: MemoryCreate,
    db: Session = Depends(get_db)
):
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Memory content cannot be blank.")
    mem = memory_service.create_memory(
        db,
        content=payload.content,
        category=payload.category or "preference"
    )
    return MemoryResponse.model_validate(mem)

@router.patch("/{memory_id}", response_model=MemoryResponse)
def update_memory(
    memory_id: str,
    payload: MemoryUpdate,
    db: Session = Depends(get_db)
):
    mem = memory_service.update_memory(
        db,
        memory_id=memory_id,
        content=payload.content,
        category=payload.category,
        is_active=payload.is_active
    )
    if not mem:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return MemoryResponse.model_validate(mem)

@router.delete("/{memory_id}")
def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db)
):
    deleted = memory_service.delete_memory(db, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return {"status": "deleted", "id": memory_id}

@router.delete("")
def clear_all_memories(db: Session = Depends(get_db)):
    count = memory_service.clear_all_memories(db)
    return {"status": "cleared", "deleted_count": count}
