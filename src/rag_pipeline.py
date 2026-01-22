"""
RAG Pipeline Module

Main orchestration layer that combines retrieval and generation.
"""

from typing import Dict, Any, Optional, List
from config import get_config, Config
from vector_store import VectorStore
from retriever import Retriever
from llm_handler import LLMHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Main RAG pipeline orchestrating retrieval and generation."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize RAG pipeline.
        
        Args:
            config: Optional Config object. If None, loads from environment.
        """
        # Load configuration
        self.config = config if config is not None else get_config()
        
        logger.info("Initializing RAG Pipeline")
        logger.info(f"Config: {self.config}")
        
        # Initialize vector store
        self.vector_store = VectorStore(
            persist_directory=self.config.chroma_persist_dir,
            embedding_model=self.config.embedding_model
        )
        
        # Initialize retriever
        self.retriever = Retriever(
            vector_store=self.vector_store,
            top_k=self.config.top_k_retrieval,
            similarity_threshold=self.config.similarity_threshold
        )
        
        # Initialize LLM handler
        self.llm_handler = LLMHandler(
            api_key=self.config.groq_api_key,
            model=self.config.groq_model
        )
        
        logger.info("RAG Pipeline initialized successfully")
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        use_reranking: bool = True,
        validate_answer: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve (overrides config)
            use_reranking: Whether to use reranking
            validate_answer: Whether to validate the answer
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        logger.info(f"Processing query: {question}")
        
        # Retrieve relevant documents
        if use_reranking:
            retrieved_docs = self.retriever.retrieve_with_reranking(
                query=question,
                top_k=top_k
            )
        else:
            retrieved_docs = self.retriever.retrieve(
                query=question,
                top_k=top_k
            )
        
        if not retrieved_docs:
            return {
                "answer": "I don't have information about that in the policy documents.",
                "sources": [],
                "retrieved_count": 0,
                "confidence": 0
            }
        
        # Format context for LLM
        context = self._format_context(retrieved_docs)
        
        # Generate answer
        if validate_answer:
            llm_result = self.llm_handler.generate_with_validation(
                query=question,
                context=context
            )
        else:
            llm_result = self.llm_handler.generate_answer(
                query=question,
                context=context
            )
        
        # Prepare response
        response = {
            "answer": llm_result["answer"],
            "sources": self._format_sources(retrieved_docs),
            "retrieved_count": len(retrieved_docs),
            "tokens_used": llm_result.get("tokens_used", 0),
            "response_time": llm_result.get("response_time", 0)
        }
        
        # Add validation info if available
        if validate_answer:
            response["validation"] = llm_result.get("validation", {})
            response["confidence"] = llm_result.get("confidence_score", 0)
        else:
            response["confidence"] = self._estimate_confidence(retrieved_docs)
        
        logger.info(f"Query processed: {len(retrieved_docs)} sources, confidence: {response['confidence']}")
        
        return response
    
    def _format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc['metadata']
            source = metadata.get('source', 'Unknown')
            section = metadata.get('section', 'General')
            
            context_parts.append(
                f"[Context {i}] Source: {source} | Section: {section}\n"
                f"{doc['text']}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def _format_sources(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source information for response.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for doc in retrieved_docs:
            metadata = doc['metadata']
            
            source = {
                "document": metadata.get('source', 'Unknown'),
                "section": metadata.get('section', 'General'),
                "similarity": round(doc['similarity'], 3),
                "text_preview": doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            }
            
            # Add optional metadata fields
            if 'version' in metadata:
                source['version'] = metadata['version']
            if 'effective_date' in metadata:
                source['effective_date'] = metadata['effective_date']
            
            sources.append(source)
        
        return sources
    
    def _estimate_confidence(self, retrieved_docs: List[Dict[str, Any]]) -> int:
        """
        Estimate confidence based on retrieval quality.
        
        Args:
            retrieved_docs: List of retrieved documents
            
        Returns:
            Confidence score (0-100)
        """
        if not retrieved_docs:
            return 0
        
        # Base confidence on average similarity
        avg_similarity = sum(doc['similarity'] for doc in retrieved_docs) / len(retrieved_docs)
        
        # Check if top result has high similarity
        top_similarity = retrieved_docs[0]['similarity']
        
        # Confidence calculation
        if top_similarity > 0.85:
            confidence = 90 + int((top_similarity - 0.85) * 100 / 3)
        elif top_similarity > 0.75:
            confidence = 75 + int((top_similarity - 0.75) * 150)
        else:
            confidence = int(avg_similarity * 75)
        
        return min(confidence, 95)  # Cap at 95
    
    def batch_query(
        self,
        questions: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Process multiple queries in batch.
        
        Args:
            questions: List of questions
            **kwargs: Additional arguments passed to query()
            
        Returns:
            List of responses
        """
        logger.info(f"Processing batch of {len(questions)} queries")
        
        responses = []
        for question in questions:
            try:
                response = self.query(question, **kwargs)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error processing question '{question}': {e}")
                responses.append({
                    "answer": f"Error processing query: {str(e)}",
                    "sources": [],
                    "error": str(e)
                })
        
        return responses
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dictionary with system statistics
        """
        vector_stats = self.vector_store.get_collection_stats()
        
        stats = {
            "total_documents": vector_stats.get("total_documents", 0),
            "embedding_model": self.config.embedding_model,
            "llm_model": self.config.groq_model,
            "chunk_size": self.config.chunk_size,
            "chunk_overlap": self.config.chunk_overlap,
            "top_k": self.config.top_k_retrieval,
            "similarity_threshold": self.config.similarity_threshold
        }
        
        if "sample_sources" in vector_stats:
            stats["indexed_sources"] = vector_stats["sample_sources"]
        
        return stats
