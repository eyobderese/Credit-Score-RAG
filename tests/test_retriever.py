"""
Unit Tests for Retriever
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retriever import Retriever


class TestRetriever:
    """Test suite for Retriever."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        mock = Mock()
        mock.similarity_search_with_relevance = Mock(return_value=[
            {
                'text': 'Test document 1',
                'metadata': {'source': 'test.md', 'section': 'Section 1'},
                'similarity': 0.9
            },
            {
                'text': 'Test document 2',
                'metadata': {'source': 'test.md', 'section': 'Section 2'},
                'similarity': 0.8
            }
        ])
        return mock
    
    @pytest.fixture
    def retriever(self, mock_vector_store):
        """Create Retriever instance with mock vector store."""
        return Retriever(
            vector_store=mock_vector_store,
            top_k=5,
            similarity_threshold=0.7
        )
    
    def test_initialization(self, retriever):
        """Test retriever initialization."""
        assert retriever.top_k == 5
        assert retriever.similarity_threshold == 0.7
    
    def test_basic_retrieval(self, retriever, mock_vector_store):
        """Test basic retrieval."""
        results = retriever.retrieve("test query")
        
        assert len(results) == 2
        assert results[0]['similarity'] == 0.9
        assert results[1]['similarity'] == 0.8
        
        # Verify vector store was called
        mock_vector_store.similarity_search_with_relevance.assert_called_once()
    
    def test_custom_top_k(self, retriever, mock_vector_store):
        """Test retrieval with custom top_k."""
        results = retriever.retrieve("test query", top_k=3)
        
        # Verify custom top_k was passed
        call_args = mock_vector_store.similarity_search_with_relevance.call_args
        assert call_args[1]['k'] == 3
    
    def test_custom_threshold(self, retriever, mock_vector_store):
        """Test retrieval with custom threshold."""
        results = retriever.retrieve("test query", threshold=0.85)
        
        # Verify custom threshold was passed
        call_args = mock_vector_store.similarity_search_with_relevance.call_args
        assert call_args[1]['threshold'] == 0.85
    
    def test_empty_results(self, mock_vector_store):
        """Test handling of empty results."""
        mock_vector_store.similarity_search_with_relevance = Mock(return_value=[])
        retriever = Retriever(mock_vector_store)
        
        results = retriever.retrieve("test query")
        assert results == []
    
    def test_reranking(self, retriever):
        """Test retrieval with reranking."""
        results = retriever.retrieve_with_reranking("credit score 620")
        
        # Results should still be returned
        assert len(results) > 0
        
        # Check for rerank scores
        for result in results:
            assert 'rerank_score' in result or 'similarity' in result
    
    def test_mmr_retrieval(self, retriever):
        """Test MMR retrieval for diversity."""
        results = retriever.retrieve_with_mmr("test query", diversity_weight=0.5)
        
        # Should return results
        assert len(results) > 0
    
    def test_text_similarity(self, retriever):
        """Test text similarity calculation."""
        text1 = "credit score requirements"
        text2 = "credit score minimum"
        
        similarity = retriever._text_similarity(text1, text2)
        
        # Should be between 0 and 1
        assert 0 <= similarity <= 1
        
        # Identical texts should have similarity 1
        assert retriever._text_similarity(text1, text1) == 1.0
    
    def test_context_formatting(self, retriever):
        """Test context formatting for LLM."""
        context = retriever.get_context_for_llm("test query")
        
        # Context should be a string
        assert isinstance(context, str)
        
        # Should contain source information
        assert "Source:" in context or "No relevant" in context


class TestSimpleRerank:
    """Test reranking functionality."""
    
    @pytest.fixture
    def retriever(self):
        """Create basic retriever for testing."""
        mock_vs = Mock()
        return Retriever(mock_vs)
    
    def test_number_matching_boost(self, retriever):
        """Test that matching numbers boost scores."""
        results = [
            {
                'text': 'Minimum credit score is 620 for conventional loans',
                'metadata': {'section': 'Credit Requirements'},
                'similarity': 0.75
            },
            {
                'text': 'General information about loans',
                'metadata': {'section': 'Overview'},
                'similarity': 0.80
            }
        ]
        
        reranked = retriever._simple_rerank("What is the 620 credit score requirement", results)
        
        # Result with matching number should get a boost
        assert reranked[0]['rerank_score'] >= results[0]['similarity']
