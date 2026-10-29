from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_name: str
    filename: str
    file_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    file_path: Optional[str] = None
    url: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

class DocumentSearchRequest(BaseModel):
    query: str
    collection_name: Optional[str] = None
    top_k: int = 4

class DocumentSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    content: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None

class CollectionSummary(BaseModel):
    name: str
    document_count: int
    total_chunks: int
