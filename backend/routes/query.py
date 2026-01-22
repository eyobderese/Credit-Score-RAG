"""
Query Routes

API endpoints for RAG query operations.
"""
import sys
from pathlib import Path
from datetime import datetime
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.query import (
    QueryRequest, QueryResponse, SourceInfo,
    BatchQueryRequest, BatchQueryResponse,
    FeedbackRequest, FeedbackResponse
)

router = APIRouter()

# In-memory feedback storage (for MVP)
feedback_store = []


def get_rag(request: Request):
    """Get RAG pipeline from app state."""
    return request.app.state.get_rag_pipeline()


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest, rag=Depends(get_rag)):
    """
    Process a natural language query about credit policies.
    
    Returns an answer with source citations and confidence score.
    """
    start_time = time.time()
    
    try:
        # Run RAG query
        result = rag.query(
            question=request.question,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            validate_answer=request.validate_answer
        )
        
        # Format sources
        sources = []
        for source in result.get("sources", []):
            sources.append(SourceInfo(
                document=source.get("document", "unknown"),
                chunk_id=source.get("chunk_id", ""),
                content=source.get("text", source.get("content", "")),
                similarity=source.get("similarity", 0.0),
                metadata=source.get("metadata", {})
            ))
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return QueryResponse(
            answer=result.get("answer", "Unable to generate answer"),
            sources=sources,
            confidence=result.get("confidence", 0),
            query_time_ms=elapsed_ms,
            retrieved_count=len(sources),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/batch", response_model=BatchQueryResponse)
async def batch_query(request: BatchQueryRequest, rag=Depends(get_rag)):
    """
    Process multiple queries in batch.
    
    Useful for evaluation and testing.
    """
    start_time = time.time()
    results = []
    
    for question in request.questions:
        try:
            query_start = time.time()
            result = rag.query(question=question, top_k=request.top_k)
            query_time = (time.time() - query_start) * 1000
            
            sources = [
                SourceInfo(
                    document=s.get("document", "unknown"),
                    chunk_id=s.get("chunk_id", ""),
                    content=s.get("text", s.get("content", "")),
                    similarity=s.get("similarity", 0.0),
                    metadata=s.get("metadata", {})
                )
                for s in result.get("sources", [])
            ]
            
            results.append(QueryResponse(
                answer=result.get("answer", ""),
                sources=sources,
                confidence=result.get("confidence", 0),
                query_time_ms=query_time,
                retrieved_count=len(sources),
                timestamp=datetime.utcnow()
            ))
        except Exception as e:
            # Include error as result
            results.append(QueryResponse(
                answer=f"Error: {str(e)}",
                sources=[],
                confidence=0,
                query_time_ms=0,
                retrieved_count=0,
                timestamp=datetime.utcnow()
            ))
    
    total_time = (time.time() - start_time) * 1000
    
    return BatchQueryResponse(results=results, total_time_ms=total_time)


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on a query response.
    
    Used for improving the system and tracking quality.
    """
    feedback_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query_id": request.query_id,
        "question": request.question,
        "answer": request.answer,
        "is_helpful": request.is_helpful,
        "feedback_text": request.feedback_text,
        "correct_answer": request.correct_answer
    }
    
    feedback_store.append(feedback_entry)
    
    return FeedbackResponse(
        success=True,
        message=f"Feedback recorded. Total feedback entries: {len(feedback_store)}"
    )


@router.get("/feedback/stats")
async def get_feedback_stats():
    """Get statistics about collected feedback."""
    if not feedback_store:
        return {
            "total_feedback": 0,
            "helpful_rate": None,
            "recent_feedback": []
        }
    
    helpful_count = sum(1 for f in feedback_store if f.get("is_helpful"))
    
    return {
        "total_feedback": len(feedback_store),
        "helpful_rate": helpful_count / len(feedback_store) if feedback_store else 0,
        "helpful_count": helpful_count,
        "not_helpful_count": len(feedback_store) - helpful_count,
        "recent_feedback": feedback_store[-10:]  # Last 10
    }
