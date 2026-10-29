import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.app.services.research_service import research_service

router = APIRouter(prefix="/research", tags=["Deep Research"])

class ResearchRequest(BaseModel):
    query: str
    max_searches: int = 3

@router.post("/deep")
async def trigger_deep_research(payload: ResearchRequest):
    """
    Executes bounded, multi-step structured deep research workflow.
    Streams progress states, source discoveries, and final synthesized report.
    """
    async def event_generator():
        async for ev in research_service.run_deep_research_stream(
            question=payload.query,
            max_searches=payload.max_searches
        ):
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
