from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.message import Message
from backend.app.schemas.chat import (
    ChatCompletionRequest,
    MessageFeedbackUpdate,
    MessageResponse
)
from backend.app.services.chat_service import chat_service

router = APIRouter(tags=["Chat Execution"])

@router.post("/chat/stream")
async def chat_stream(
    payload: ChatCompletionRequest,
    db: Session = Depends(get_db)
):
    """
    Primary real-time conversational SSE streaming endpoint.
    Streams token by token with tool execution indicators, citation linking, and cancellation.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be blank.")

    generator = chat_service.stream_chat_response(
        db=db,
        conversation_id=payload.conversation_id,
        user_message=payload.message,
        model_id=payload.model_id,
        system_prompt=payload.system_prompt,
        web_search=payload.web_search,
        deep_research=payload.deep_research,
        collection_name=payload.collection_name,
        attachments=payload.attachments,
        temperature=payload.temperature or 0.7,
    )

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.post("/messages/{message_id}/feedback")
def set_message_feedback(
    message_id: str,
    payload: MessageFeedbackUpdate,
    db: Session = Depends(get_db)
):
    """Persists user rating (like, dislike, none) for a response."""
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

    msg.feedback = payload.feedback
    db.commit()
    return {"status": "ok", "message_id": message_id, "feedback": msg.feedback}
