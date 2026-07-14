from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    session_id: str

class SourceDocument(BaseModel):
    page: int
    text: str
    similarity_score: float
    cosine_distance: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    session_id: str
