"""
Vector Store Module

Manages ChromaDB vector database for document embeddings and similarity search.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector database operations for RAG system."""
    
    def __init__(
        self,
        persist_directory: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "credit_policies"
    ):
        """
        Initialize vector store with ChromaDB.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedding_model: Name of sentence-transformers model
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at: {persist_directory}")
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        # Using cosine distance for better similarity interpretation
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Credit scoring and underwriting policies",
                "hnsw:space": "cosine"
            }
        )
        
        logger.info(f"Collection '{collection_name}' ready with {self.collection.count()} documents")
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        # Extract texts and metadata
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        ).tolist()
        
        # Generate IDs
        ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Add to collection
        logger.info("Adding to ChromaDB...")
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully added {len(documents)} documents")
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Search query text
            k: Number of results to return
            threshold: Minimum similarity score (0-1). Results below this are filtered out.
            filter_dict: Optional metadata filters
            
        Returns:
            List of search results with text, metadata, and similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict
        )
        
        # Format results
        formatted_results = []
        
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                # Calculate similarity score
                # For cosine distance, distance = 1 - cosine_similarity
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Convert cosine distance back to similarity
                
                # Apply threshold if specified
                if threshold is not None and similarity < threshold:
                    continue
                
                result = {
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity,
                    'id': results['ids'][0][i]
                }
                formatted_results.append(result)
        
        logger.info(f"Found {len(formatted_results)} results (threshold: {threshold})")
        return formatted_results
    
    def similarity_search_with_relevance(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search and return only relevant results.
        
        Args:
            query: Search query text
            k: Number of results to retrieve initially
            threshold: Minimum similarity score to be considered relevant
            
        Returns:
            List of relevant search results sorted by similarity
        """
        results = self.similarity_search(query, k=k, threshold=threshold)
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        logger.warning(f"Deleting collection: {self.collection_name}")
        self.client.delete_collection(name=self.collection_name)
    
    def reset_collection(self) -> None:
        """Reset the collection by deleting and recreating it."""
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Credit scoring and underwriting policies"}
        )
        logger.info(f"Collection '{self.collection_name}' reset")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        
        # Get sample to analyze metadata
        sample = self.collection.peek(limit=min(10, count))
        
        stats = {
            "total_documents": count,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
        }
        
        # Extract unique sources if available
        if sample['metadatas']:
            sources = set()
            for metadata in sample['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])
            stats["sample_sources"] = list(sources)
        
        return stats
