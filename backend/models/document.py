"""
Pydantic models for document-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    MARKDOWN = "markdown"
    PDF = "pdf"
    TEXT = "text"


class DocumentInfo(BaseModel):
    """Information about an ingested document."""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType = Field(..., description="Document type")
    chunk_count: int = Field(..., ge=0, description="Number of chunks created")
    total_characters: int = Field(..., ge=0, description="Total character count")
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DocumentStats(BaseModel):
    """Statistics about all documents in the system."""
    total_documents: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=0)
    total_characters: int = Field(..., ge=0)
    documents_by_type: Dict[str, int] = Field(default_factory=dict)
    last_ingestion: Optional[datetime] = None
    vector_store_size_mb: Optional[float] = None


class UploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool = Field(True)
    document_id: str = Field(..., description="Assigned document ID")
    filename: str = Field(..., description="Uploaded filename")
    chunks_created: int = Field(..., ge=0)
    processing_time_ms: float = Field(...)
    message: str = Field("Document ingested successfully")


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentInfo] = Field(default_factory=list)
    total_count: int = Field(..., ge=0)


class ChunkInfo(BaseModel):
    """Information about a document chunk."""
    chunk_id: str = Field(...)
    content: str = Field(...)
    start_char: int = Field(..., ge=0)
    end_char: int = Field(..., ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentDetailResponse(BaseModel):
    """Detailed response for a single document."""
    document: DocumentInfo
    chunks: List[ChunkInfo] = Field(default_factory=list)
    sample_content: Optional[str] = Field(None, description="First 1000 chars of document")
