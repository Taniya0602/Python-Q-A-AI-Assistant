from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000, description="Python-related question")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of sources to retrieve")

    model_config = {"json_schema_extra": {"example": {"question": "How do I reverse a list in Python?"}}}


class Source(BaseModel):
    title: str
    score: float
    snippet: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]
    model: str
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    vector_store_loaded: bool
    total_documents: int
    model: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
