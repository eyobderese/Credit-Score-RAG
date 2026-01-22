"""
Document Processing Module

Handles loading, chunking, and preprocessing of policy documents.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Processes markdown documents for RAG system."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Maximum size of text chunks in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter optimized for markdown
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n## ",  # Main sections
                "\n\n### ",  # Subsections
                "\n\n",  # Paragraphs
                "\n",  # Lines
                " ",  # Words
                ""  # Characters
            ]
        )
        
    def load_documents(self, directory: Path) -> List[Document]:
        """
        Load all markdown documents from a directory.
        
        Args:
            directory: Path to directory containing markdown files
            
        Returns:
            List of Document objects with content and metadata
        """
        documents = []
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all markdown files
        md_files = list(directory.glob("*.md"))
        
        if not md_files:
            logger.warning(f"No markdown files found in {directory}")
            return documents
        
        for file_path in md_files:
            logger.info(f"Loading: {file_path.name}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from document
            metadata = self._extract_metadata(content, file_path)
            
            # Create document object
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
            
        logger.info(f"Loaded {len(documents)} documents")
        return documents
    
    def _extract_metadata(self, content: str, file_path: Path) -> Dict[str, str]:
        """
        Extract metadata from document content.
        
        Args:
            content: Document text content
            file_path: Path to the source file
            
        Returns:
            Dictionary of metadata fields
        """
        metadata = {
            "source": file_path.name,
            "file_path": str(file_path)
        }
        
        # Extract document title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        # Extract version from Document Information section
        version_match = re.search(r'\*\*Version:\*\*\s+(.+)$', content, re.MULTILINE)
        if version_match:
            metadata["version"] = version_match.group(1).strip()
        
        # Extract effective date
        date_match = re.search(r'\*\*Effective Date:\*\*\s+(.+)$', content, re.MULTILINE)
        if date_match:
            metadata["effective_date"] = date_match.group(1).strip()
        
        # Extract department
        dept_match = re.search(r'\*\*Department:\*\*\s+(.+)$', content, re.MULTILINE)
        if dept_match:
            metadata["department"] = dept_match.group(1).strip()
        
        return metadata
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks while preserving context.
        
        Args:
            documents: List of Document objects to split
            
        Returns:
            List of chunked Document objects with enhanced metadata
        """
        all_chunks = []
        
        for doc in documents:
            # Split the document
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk-specific metadata
            for i, chunk in enumerate(chunks):
                # Preserve original metadata
                chunk.metadata.update(doc.metadata)
                
                # Add chunk information
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(chunks)
                
                # Extract section heading from chunk if available
                section = self._extract_section_heading(chunk.page_content)
                if section:
                    chunk.metadata["section"] = section
                
                all_chunks.append(chunk)
        
        logger.info(f"Split into {len(all_chunks)} chunks")
        return all_chunks
    
    def _extract_section_heading(self, text: str) -> Optional[str]:
        """
        Extract the main section heading from a chunk of text.
        
        Args:
            text: Text chunk
            
        Returns:
            Section heading or None
        """
        # Look for markdown headings at various levels
        for pattern in [r'^##\s+(.+)$', r'^###\s+(.+)$', r'^####\s+(.+)$']:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def process_directory(self, directory: Path) -> List[Document]:
        """
        Complete processing pipeline: load and split documents.
        
        Args:
            directory: Path to directory containing markdown files
            
        Returns:
            List of processed document chunks ready for embedding
        """
        logger.info(f"Processing documents from {directory}")
        
        # Load documents
        documents = self.load_documents(directory)
        
        if not documents:
            return []
        
        # Split into chunks
        chunks = self.split_documents(documents)
        
        logger.info(f"Processing complete: {len(chunks)} chunks from {len(documents)} documents")
        return chunks
