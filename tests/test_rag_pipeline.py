"""
Integration Tests for RAG Pipeline
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_data import TEST_QUERIES


class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline (requires actual setup)."""
    
    @pytest.mark.integration
    def test_end_to_end_query(self):
        """Test complete query flow (requires vector DB setup)."""
        # Skip if not in integration test mode
        pytest.skip("Integration test - requires full setup")
        
        from rag_pipeline import RAGPipeline
        
        rag = RAGPipeline()
        response = rag.query("What is the minimum credit score for FHA loans?")
        
        assert 'answer' in response
        assert 'sources' in response
        assert len(response['sources']) > 0
    
    @pytest.mark.integration
    def test_batch_queries(self):
        """Test batch query processing."""
        pytest.skip("Integration test - requires full setup")
        
        from rag_pipeline import RAGPipeline
        
        rag = RAGPipeline()
        questions = [q['question'] for q in TEST_QUERIES[:3]]
        
        responses = rag.batch_query(questions)
        
        assert len(responses) == 3
        for response in responses:
            assert 'answer' in response
    
    def test_query_validation(self):
        """Test query validation logic."""
        from rag_pipeline import RAGPipeline
        
        # Mock the components
        with patch('rag_pipeline.VectorStore'):
            with patch('rag_pipeline.Retriever'):
                with patch('rag_pipeline.LLMHandler'):
                    # This should not raise an error
                    rag = RAGPipeline()
                    assert rag is not None


class TestResponseFormatting:
    """Test response formatting."""
    
    def test_source_formatting(self):
        """Test source information formatting."""
        from rag_pipeline import RAGPipeline
        
        # Create instance without full initialization
        with patch('rag_pipeline.VectorStore'):
            with patch('rag_pipeline.Retriever'):
                with patch('rag_pipeline.LLMHandler'):
                    rag = RAGPipeline()
                    
                    # Test source formatting
                    retrieved_docs = [
                        {
                            'text': 'Test content',
                            'metadata': {
                                'source': 'test.md',
                                'section': 'Test Section',
                                'version': '1.0'
                            },
                            'similarity': 0.85
                        }
                    ]
                    
                    sources = rag._format_sources(retrieved_docs)
                    
                    assert len(sources) == 1
                    assert sources[0]['document'] == 'test.md'
                    assert sources[0]['section'] == 'Test Section'
                    assert sources[0]['version'] == '1.0'
                    assert sources[0]['similarity'] == 0.850
    
    def test_confidence_estimation(self):
        """Test confidence score calculation."""
        from rag_pipeline import RAGPipeline
        
        with patch('rag_pipeline.VectorStore'):
            with patch('rag_pipeline.Retriever'):
                with patch('rag_pipeline.LLMHandler'):
                    rag = RAGPipeline()
                    
                    # High similarity results
                    high_sim_docs = [
                        {'similarity': 0.90},
                        {'similarity': 0.88}
                    ]
                    confidence = rag._estimate_confidence(high_sim_docs)
                    assert confidence >= 85
                    
                    # Low similarity results
                    low_sim_docs = [
                        {'similarity': 0.65},
                        {'similarity': 0.60}
                    ]
                    confidence = rag._estimate_confidence(low_sim_docs)
                    assert confidence < 75
                    
                    # Empty results
                    confidence = rag._estimate_confidence([])
                    assert confidence == 0


class TestErrorHandling:
    """Test error handling in RAG pipeline."""
    
    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        from rag_pipeline import RAGPipeline
        
        with patch('rag_pipeline.VectorStore'):
            with patch('rag_pipeline.Retriever') as mock_retriever:
                # Mock empty retrieval results
                mock_instance = Mock()
                mock_instance.retrieve_with_reranking = Mock(return_value=[])
                mock_retriever.return_value = mock_instance
                
                with patch('rag_pipeline.LLMHandler'):
                    rag = RAGPipeline()
                    
                    response = rag.query("test")
                    
                    # Should handle gracefully
                    assert 'answer' in response
                    assert response['retrieved_count'] == 0
    
    def test_stats_retrieval(self):
        """Test system statistics retrieval."""
        from rag_pipeline import RAGPipeline
        
        with patch('rag_pipeline.VectorStore') as mock_vs:
            mock_instance = Mock()
            mock_instance.get_collection_stats = Mock(return_value={
                'total_documents': 100,
                'sample_sources': ['test1.md', 'test2.md']
            })
            mock_vs.return_value = mock_instance
            
            with patch('rag_pipeline.Retriever'):
                with patch('rag_pipeline.LLMHandler'):
                    rag = RAGPipeline()
                    
                    stats = rag.get_stats()
                    
                    assert 'total_documents' in stats
                    assert stats['total_documents'] == 100
                    assert 'indexed_sources' in stats
