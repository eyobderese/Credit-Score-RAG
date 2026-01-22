"""
FastAPI Main Application

Entry point for the Credit Scoring RAG API.
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add src to path for importing existing modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Add backend to path for importing models and routes
sys.path.insert(0, str(Path(__file__).parent))

from routes import query_router, documents_router, evaluation_router, experiments_router


# Global RAG pipeline instance
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    global rag_pipeline
    
    # Startup: Initialize RAG pipeline
    print("🚀 Initializing RAG Pipeline...")
    try:
        from rag_pipeline import RAGPipeline
        rag_pipeline = RAGPipeline()
        print("✅ RAG Pipeline initialized successfully")
    except Exception as e:
        print(f"⚠️ RAG Pipeline initialization error: {e}")
        print("   Some features may be unavailable until documents are ingested")
    
    yield
    
    # Shutdown: Cleanup
    print("👋 Shutting down RAG Pipeline...")
    rag_pipeline = None


# Create FastAPI app
app = FastAPI(
    title="Credit Scoring RAG API",
    description="""
    A production-ready **Retrieval-Augmented Generation (RAG)** API for answering
    questions about credit policies, scoring rules, and underwriting guidelines.
    
    ## Features
    
    - **Query**: Ask natural language questions about credit policies
    - **Documents**: Upload and manage policy documents
    - **Evaluation**: Run evaluations and track metrics
    - **Experiments**: Compare different RAG configurations
    
    ## Authentication
    
    Currently no authentication required (internal use only).
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get RAG pipeline
def get_rag_pipeline():
    """Dependency injection for RAG pipeline."""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="RAG Pipeline not initialized. Please ingest documents first."
        )
    return rag_pipeline


# Make it available to routes
app.state.get_rag_pipeline = get_rag_pipeline


# Include routers
app.include_router(query_router, prefix="/api/query", tags=["Query"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(evaluation_router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(experiments_router, prefix="/api/experiments", tags=["Experiments"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Credit Scoring RAG API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    global rag_pipeline
    
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "up",
            "rag_pipeline": "up" if rag_pipeline is not None else "not_initialized"
        }
    }
    
    # Check vector store if pipeline exists
    if rag_pipeline is not None:
        try:
            stats = rag_pipeline.get_stats()
            status["components"]["vector_store"] = "up"
            status["documents_indexed"] = stats.get("total_documents", 0)
            status["chunks_indexed"] = stats.get("total_chunks", 0)
        except Exception as e:
            status["components"]["vector_store"] = f"error: {str(e)}"
    
    return status


@app.get("/api/config", tags=["Configuration"])
async def get_config():
    """Get current RAG configuration."""
    try:
        from config import get_config
        config = get_config()
        return {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k_retrieval": config.top_k_retrieval,
            "similarity_threshold": config.similarity_threshold,
            "embedding_model": config.embedding_model,
            "llm_model": config.groq_model,
            "chroma_persist_dir": config.chroma_persist_dir
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
