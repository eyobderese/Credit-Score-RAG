"""
Document Routes

API endpoints for document management operations.
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import hashlib
import tempfile
import os
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.document import (
    DocumentInfo, DocumentStats, UploadResponse,
    DocumentListResponse, DocumentDetailResponse, DocumentType, ChunkInfo
)

router = APIRouter()

# In-memory document registry (for MVP)
document_registry = {}


def get_rag(request: Request):
    """Get RAG pipeline from app state."""
    try:
        return request.app.state.get_rag_pipeline()
    except:
        return None


def determine_doc_type(filename: str) -> DocumentType:
    """Determine document type from filename."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext == "pdf":
        return DocumentType.PDF
    elif ext in ["md", "markdown"]:
        return DocumentType.MARKDOWN
    else:
        return DocumentType.TEXT


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    request: Request = None
):
    """
    Upload and ingest a document into the RAG system.
    
    Supports PDF and Markdown files.
    """
    start_time = time.time()
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    allowed_extensions = [".pdf", ".md", ".markdown", ".txt"]
    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Generate document ID
        doc_id = hashlib.md5(f"{file.filename}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        
        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Import and use document processor
            from document_processor import DocumentProcessor
            from config import get_config
            
            config = get_config()
            processor = DocumentProcessor(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
            
            # Load and process document
            docs = processor.load_single_file(tmp_path, original_filename=file.filename)
            chunks = processor.split_documents(docs)
            
            # Get RAG pipeline and add to vector store
            rag = get_rag(request)
            if rag and hasattr(rag, 'vector_store'):
                # Add document_id to chunk metadata
                for chunk in chunks:
                    chunk.metadata["document_id"] = doc_id
                # Add chunks to vector store (chunks are already Document objects)
                rag.vector_store.add_documents(chunks)
            
            # Register document
            doc_info = DocumentInfo(
                id=doc_id,
                filename=file.filename,
                document_type=determine_doc_type(file.filename),
                chunk_count=len(chunks),
                total_characters=sum(len(c.page_content) for c in chunks),
                ingested_at=datetime.utcnow(),
                metadata={"original_size": len(content)}
            )
            document_registry[doc_id] = doc_info
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return UploadResponse(
                success=True,
                document_id=doc_id,
                filename=file.filename,
                chunks_created=len(chunks),
                processing_time_ms=elapsed_ms,
                message=f"Successfully ingested {file.filename} with {len(chunks)} chunks"
            )
            
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    List all ingested documents.
    """
    documents = list(document_registry.values())
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.get("/stats", response_model=DocumentStats)
async def get_document_stats(request: Request):
    """
    Get statistics about documents in the system.
    """
    documents = list(document_registry.values())
    
    # Count by type
    by_type = {}
    for doc in documents:
        doc_type = doc.document_type.value
        by_type[doc_type] = by_type.get(doc_type, 0) + 1
    
    # Get vector store stats if available
    rag = get_rag(request)
    total_chunks = sum(doc.chunk_count for doc in documents)
    total_chars = sum(doc.total_characters for doc in documents)
    
    if rag:
        try:
            stats = rag.get_stats()
            total_chunks = stats.get("total_chunks", total_chunks)
        except:
            pass
    
    last_ingestion = None
    if documents:
        last_ingestion = max(doc.ingested_at for doc in documents)
    
    return DocumentStats(
        total_documents=len(documents),
        total_chunks=total_chunks,
        total_characters=total_chars,
        documents_by_type=by_type,
        last_ingestion=last_ingestion
    )


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """
    Get information about a specific document.
    """
    if doc_id not in document_registry:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document_registry[doc_id]


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, request: Request):
    """
    Delete a document from the system.
    
    Note: This removes registr but vector store cleanup requires re-indexing.
    """
    if doc_id not in document_registry:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = document_registry.pop(doc_id)
    
    return {
        "success": True,
        "message": f"Document {doc.filename} removed from registry",
        "note": "Vector store entries remain until full re-indexing"
    }


@router.post("/reingest")
async def reingest_all_documents(request: Request):
    """
    Re-ingest all documents from the data/raw directory.
    """
    try:
        # Import ingestion script
        from ingest_documents import main as ingest_main
        
        # Clear registry
        document_registry.clear()
        
        # Run ingestion
        ingest_main()
        
        return {
            "success": True,
            "message": "Documents re-ingested successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-ingestion failed: {str(e)}")
