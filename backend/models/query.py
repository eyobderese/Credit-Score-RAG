"""
Pydantic models for query-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str = Field(..., min_length=1, description="The question to ask")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    use_reranking: bool = Field(True, description="Whether to use reranking")
    validate_answer: bool = Field(False, description="Whether to validate answer against sources")


class SourceInfo(BaseModel):
    """Information about a source document."""
    document: str = Field(..., description="Document name")
    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Source content snippet")
    similarity: float = Field(..., ge=0, le=1, description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceInfo] = Field(default_factory=list, description="Source citations")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score")
    query_time_ms: float = Field(..., description="Query processing time in milliseconds")
    retrieved_count: int = Field(..., description="Number of chunks retrieved")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchQueryRequest(BaseModel):
    """Request model for batch queries."""
    questions: List[str] = Field(..., min_length=1, description="List of questions")
    top_k: Optional[int] = Field(5, ge=1, le=20)


class BatchQueryResponse(BaseModel):
    """Response model for batch queries."""
    results: List[QueryResponse] = Field(default_factory=list)
    total_time_ms: float = Field(..., description="Total processing time")


class FeedbackRequest(BaseModel):
    """Request model for query feedback."""
    query_id: Optional[str] = Field(None, description="Query identifier")
    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="The answer that was given")
    is_helpful: bool = Field(..., description="Whether the answer was helpful")
    feedback_text: Optional[str] = Field(None, description="Additional feedback text")
    correct_answer: Optional[str] = Field(None, description="The correct answer if provided")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    success: bool = Field(True)
    message: str = Field("Feedback recorded successfully")
