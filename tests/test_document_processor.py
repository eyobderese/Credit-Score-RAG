"""
Unit Tests for Document Processor
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_processor import DocumentProcessor
from langchain_core.documents import Document


class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance."""
        return DocumentProcessor(chunk_size=500, chunk_overlap=50)
    
    def test_initialization(self, processor):
        """Test processor initialization."""
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        assert processor.text_splitter is not None
    
    def test_metadata_extraction(self, processor):
        """Test metadata extraction from document."""
        content = """# Credit Scoring Manual

## Document Information
**Version:** 3.2  
**Effective Date:** January 2026  
**Department:** Risk Management  

## Content
Some policy content here.
"""
        file_path = Path("/test/credit_scoring_manual.md")
        metadata = processor._extract_metadata(content, file_path)
        
        assert metadata['source'] == "credit_scoring_manual.md"
        assert metadata['title'] == "Credit Scoring Manual"
        assert metadata['version'] == "3.2"
        assert metadata['effective_date'] == "January 2026"
        assert metadata['department'] == "Risk Management"
    
    def test_section_extraction(self, processor):
        """Test section heading extraction."""
        text = """## Credit Score Requirements

Some content about credit scores.

### Minimum Scores
More specific content.
"""
        section = processor._extract_section_heading(text)
        assert section == "Credit Score Requirements"
    
    def test_document_splitting(self, processor):
        """Test document splitting."""
        # Create a test document
        content = "Section 1.\n\n" * 100  # Long enough to split
        doc = Document(
            page_content=content,
            metadata={"source": "test.md"}
        )
        
        chunks = processor.split_documents([doc])
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should have metadata
        for chunk in chunks:
            assert 'source' in chunk.metadata
            assert 'chunk_index' in chunk.metadata
            assert 'total_chunks' in chunk.metadata
    
    def test_empty_document_handling(self, processor):
        """Test handling of empty documents."""
        chunks = processor.split_documents([])
        assert chunks == []


class TestDocumentLoading:
    """Test document loading functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create DocumentProcessor instance."""
        return DocumentProcessor()
    
    def test_nonexistent_directory(self, processor):
        """Test loading from non-existent directory."""
        with pytest.raises(FileNotFoundError):
            processor.load_documents(Path("/nonexistent/path"))
    
    def test_empty_directory(self, processor, tmp_path):
        """Test loading from empty directory."""
        docs = processor.load_documents(tmp_path)
        assert docs == []
