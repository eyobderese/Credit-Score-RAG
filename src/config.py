"""
Configuration Management Module

Loads and manages environment variables and system configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class Config:
    """Central configuration class for the RAG system."""
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize configuration by loading environment variables.
        
        Args:
            env_path: Optional path to .env file. If None, uses default location.
        """
        # Load environment variables
        if env_path:
            load_dotenv(env_path)
        else:
            # Load from project root
            project_root = Path(__file__).parent.parent
            load_dotenv(project_root / ".env")
        
        # Groq API Configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # Embedding Model
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # RAG Configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.top_k_retrieval = int(os.getenv("TOP_K_RETRIEVAL", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
        
        # ChromaDB Configuration
        project_root = Path(__file__).parent.parent
        default_chroma_dir = project_root / "chroma_db"
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(default_chroma_dir))
        
        # Data paths
        self.data_dir = project_root / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        
    def validate(self) -> bool:
        """
        Validate that all required configuration is present and valid.
        
        Returns:
            True if configuration is valid, raises ValueError otherwise.
        """
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        
        if self.chunk_overlap < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        
        if self.top_k_retrieval <= 0:
            raise ValueError("TOP_K_RETRIEVAL must be positive")
        
        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1")
        
        return True
    
    def __repr__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        return (
            f"Config(\n"
            f"  groq_model='{self.groq_model}',\n"
            f"  embedding_model='{self.embedding_model}',\n"
            f"  chunk_size={self.chunk_size},\n"
            f"  chunk_overlap={self.chunk_overlap},\n"
            f"  top_k_retrieval={self.top_k_retrieval},\n"
            f"  similarity_threshold={self.similarity_threshold},\n"
            f"  chroma_persist_dir='{self.chroma_persist_dir}'\n"
            f")"
        )


# Global config instance
_config_instance: Optional[Config] = None


def get_config(env_path: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance.
    
    Args:
        env_path: Optional path to .env file.
        
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_path)
        _config_instance.validate()
    return _config_instance
