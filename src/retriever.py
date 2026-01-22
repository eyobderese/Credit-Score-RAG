"""
Retrieval Module

Implements advanced retrieval strategies for the RAG system.
"""

from typing import List, Dict, Any, Optional
from vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """Advanced retrieval component for RAG system."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize retriever.
        
        Args:
            vector_store: VectorStore instance
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score for results
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User query
            top_k: Override default top_k
            threshold: Override default similarity threshold
            
        Returns:
            List of relevant documents with metadata and scores
        """
        k = top_k if top_k is not None else self.top_k
        thresh = threshold if threshold is not None else self.similarity_threshold
        
        logger.info(f"Retrieving top {k} documents (threshold: {thresh})")
        
        # Perform similarity search
        results = self.vector_store.similarity_search_with_relevance(
            query=query,
            k=k,
            threshold=thresh
        )
        
        return results
    
    def retrieve_with_reranking(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and rerank results based on query-specific criteria.
        
        Args:
            query: User query
            top_k: Override default top_k
            threshold: Override default similarity threshold
            
        Returns:
            Reranked list of relevant documents
        """
        # First, retrieve more results than needed for reranking
        retrieve_k = (top_k or self.top_k) * 2
        
        results = self.retrieve(
            query=query,
            top_k=retrieve_k,
            threshold=threshold
        )
        
        # Simple reranking based on metadata signals
        reranked = self._simple_rerank(query, results)
        
        # Return top_k after reranking
        final_k = top_k if top_k is not None else self.top_k
        return reranked[:final_k]
    
    def _simple_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Simple reranking heuristic based on metadata and query terms.
        
        Args:
            query: Original user query
            results: Initial results from similarity search
            
        Returns:
            Reranked results
        """
        query_lower = query.lower()
        
        for result in results:
            score = result['similarity']
            text_lower = result['text'].lower()
            
            # Boost if document section matches query terms
            if 'section' in result['metadata']:
                section_lower = result['metadata']['section'].lower()
                # Check for exact query term matches in section
                query_terms = query_lower.split()
                section_matches = sum(1 for term in query_terms if term in section_lower)
                if section_matches > 0:
                    score += 0.05 * section_matches
            
            # Boost if query contains specific numbers/thresholds and text does too
            import re
            query_numbers = re.findall(r'\d+', query_lower)
            text_numbers = re.findall(r'\d+', text_lower)
            number_overlap = len(set(query_numbers) & set(text_numbers))
            if number_overlap > 0:
                score += 0.03 * number_overlap
            
            # Store adjusted score
            result['rerank_score'] = min(score, 1.0)  # Cap at 1.0
        
        # Sort by rerank score
        results.sort(key=lambda x: x.get('rerank_score', x['similarity']), reverse=True)
        
        return results
    
    def retrieve_with_mmr(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        diversity_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with Maximal Marginal Relevance for diversity.
        
        Args:
            query: User query
            top_k: Override default top_k
            threshold: Override default similarity threshold
            diversity_weight: Weight for diversity (0-1, higher = more diverse)
            
        Returns:
            Diverse list of relevant documents
        """
        # Retrieve more candidates for MMR
        retrieve_k = (top_k or self.top_k) * 3
        
        candidates = self.retrieve(
            query=query,
            top_k=retrieve_k,
            threshold=threshold
        )
        
        if not candidates:
            return []
        
        # MMR selection
        selected = []
        final_k = top_k if top_k is not None else self.top_k
        
        # Start with highest similarity
        selected.append(candidates[0])
        remaining = candidates[1:]
        
        while len(selected) < final_k and remaining:
            best_score = -1
            best_idx = 0
            
            for idx, candidate in enumerate(remaining):
                # Relevance to query
                relevance = candidate['similarity']
                
                # Diversity: max similarity to already selected
                max_sim_to_selected = max(
                    self._text_similarity(candidate['text'], s['text'])
                    for s in selected
                )
                
                # MMR score
                mmr_score = (
                    (1 - diversity_weight) * relevance -
                    diversity_weight * max_sim_to_selected
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity based on word overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_context_for_llm(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_reranking: bool = True
    ) -> str:
        """
        Retrieve and format context for LLM consumption.
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            use_reranking: Whether to use reranking
            
        Returns:
            Formatted context string for LLM
        """
        # Retrieve documents
        if use_reranking:
            results = self.retrieve_with_reranking(query, top_k)
        else:
            results = self.retrieve(query, top_k)
        
        if not results:
            return "No relevant policy documents found for this query."
        
        # Format context
        context_parts = []
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source = metadata.get('source', 'Unknown')
            section = metadata.get('section', 'General')
            
            context_parts.append(
                f"[Context {i}] Source: {source} | Section: {section}\n"
                f"{result['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
