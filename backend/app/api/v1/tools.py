from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.tool_registry import tool_registry

router = APIRouter(prefix="/tools", tags=["Tools & MCP"])

class ToolExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@router.get("")
def list_available_tools():
    """Returns all declared tools and parameter schemas."""
    return tool_registry.list_tools()

@router.post("/execute")
async def execute_tool(
    payload: ToolExecuteRequest,
    db: Session = Depends(get_db)
):
    """Executes a declared tool with argument validation and audit logging."""
    return await tool_registry.execute_tool(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        db=db
    )
