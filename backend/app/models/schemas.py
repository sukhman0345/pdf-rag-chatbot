from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    query: str

class SourceDocument(BaseModel):
    page: int
    text: str
    similarity_score: float
    cosine_distance: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
