"""
Credit Scoring RAG System

A production-ready Retrieval-Augmented Generation system for answering
questions about credit policies, scoring rules, and underwriting guidelines.
"""

__version__ = "1.0.0"
__author__ = "Credit Risk Team"

from .config import Config
from .rag_pipeline import RAGPipeline

__all__ = ["Config", "RAGPipeline"]
