from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.memory import Memory

class MemoryService:
    def list_memories(self, db: Session, active_only: bool = False) -> List[Memory]:
        query = db.query(Memory)
        if active_only:
            query = query.filter(Memory.is_active == True)
        return query.order_by(Memory.created_at.desc()).all()

    def get_memory(self, db: Session, memory_id: str) -> Optional[Memory]:
        return db.query(Memory).filter(Memory.id == memory_id).first()

    def create_memory(
        self,
        db: Session,
        content: str,
        category: str = "preference",
        confidence: float = 1.0,
        source_conversation_id: Optional[str] = None
    ) -> Memory:
        mem = Memory(
            content=content.strip(),
            category=category,
            confidence=confidence,
            is_active=True,
            source_conversation_id=source_conversation_id
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        return mem

    def update_memory(
        self,
        db: Session,
        memory_id: str,
        content: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Memory]:
        mem = self.get_memory(db, memory_id)
        if not mem:
            return None
        if content is not None:
            mem.content = content.strip()
        if category is not None:
            mem.category = category
        if is_active is not None:
            mem.is_active = is_active
        db.commit()
        db.refresh(mem)
        return mem

    def delete_memory(self, db: Session, memory_id: str) -> bool:
        mem = self.get_memory(db, memory_id)
        if not mem:
            return False
        db.delete(mem)
        db.commit()
        return True

    def clear_all_memories(self, db: Session) -> int:
        count = db.query(Memory).delete()
        db.commit()
        return count

    def get_relevant_memories_prompt(self, db: Session, query: str) -> Tuple_Prompt:
        """
        Retrieves active memories and formats a context injection string for the system prompt.
        """
        active_mems = self.list_memories(db, active_only=True)
        if not active_mems:
            return "", []

        mem_texts = [f"- [{m.category}] {m.content}" for m in active_mems]
        formatted = "User Preferences & Personalization Context:\n" + "\n".join(mem_texts)
        return formatted, [m.id for m in active_mems]

Tuple_Prompt = tuple[str, List[str]]

memory_service = MemoryService()
