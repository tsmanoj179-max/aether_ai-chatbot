from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageResponse
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    query: Optional[str] = Query(None, description="Search term for conversation title"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    db_query = db.query(Conversation)
    if query:
        db_query = db_query.filter(Conversation.title.ilike(f"%{query}%"))
    if folder:
        db_query = db_query.filter(Conversation.folder == folder)
    else:
        # Exclude CLI sessions from the main web conversation list
        db_query = db_query.filter(
            ~Conversation.title.ilike("CLI Session%"),
            (Conversation.folder != "cli") | (Conversation.folder.is_(None))
        )

    # Pinned first, then by updated_at descending
    conversations = (
        db_query
        .order_by(Conversation.pinned.desc(), Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for c in conversations:
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        results.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                pinned=c.pinned,
                folder=c.folder,
                model_id=c.model_id,
                system_prompt=c.system_prompt,
                message_count=len(c.messages),
                last_message=last_msg.content[:80] if last_msg else None
            )
        )
    return results

@router.post("", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db)
):
    conv = Conversation(
        title=payload.title or "New Conversation",
        model_id=payload.model_id or "aether-mock-omni",
        system_prompt=payload.system_prompt,
        folder=payload.folder
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        pinned=conv.pinned,
        folder=conv.folder,
        model_id=conv.model_id,
        system_prompt=conv.system_prompt,
        message_count=0,
        last_message=None
    )

@router.get("/{conversation_id}")
def get_conversation_details(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = [
        MessageResponse.model_validate(m) for m in conv.messages
    ]

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "pinned": conv.pinned,
        "folder": conv.folder,
        "model_id": conv.model_id,
        "system_prompt": conv.system_prompt,
        "messages": messages
    }

@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if payload.title is not None:
        conv.title = payload.title.strip()
    if payload.pinned is not None:
        conv.pinned = payload.pinned
    if payload.folder is not None:
        conv.folder = payload.folder
    if payload.model_id is not None:
        conv.model_id = payload.model_id
    if payload.system_prompt is not None:
        conv.system_prompt = payload.system_prompt

    db.commit()
    db.refresh(conv)

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        pinned=conv.pinned,
        folder=conv.folder,
        model_id=conv.model_id,
        system_prompt=conv.system_prompt,
        message_count=len(conv.messages)
    )

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conv)
    db.commit()
    return {"status": "deleted", "id": conversation_id}

@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if format == "json":
        data = {
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "model_id": conv.model_id,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                    "model_used": m.model_used,
                    "citations": m.citations
                }
                for m in conv.messages
            ]
        }
        return data

    # Markdown export
    lines = [f"# {conv.title}\n\n*Created on {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n\n---\n"]
    for m in conv.messages:
        role_label = "**User**" if m.role == "user" else f"**Assistant ({m.model_used or 'AI'})**"
        lines.append(f"\n### {role_label}\n\n{m.content}\n")
        if m.citations:
            lines.append("\n**Sources Cited:**\n")
            for c in m.citations:
                lines.append(f"- [{c.get('title', 'Source')}]({c.get('url', '#')})\n")

    return Response(
        content="".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=conversation-{conv.id[:8]}.md"}
    )
