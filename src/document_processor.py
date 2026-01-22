"""
Document Processing Module

Handles loading, chunking, and preprocessing of policy documents.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import tempfile
import os
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
        Load all markdown and PDF documents from a directory.
        
        Args:
            directory: Path to directory containing files
            
        Returns:
            List of Document objects with content and metadata
        """
        documents = []
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all markdown and PDF files
        md_files = list(directory.glob("*.md"))
        pdf_files = list(directory.glob("*.pdf"))
        
        all_files = md_files + pdf_files
        
        if not all_files:
            logger.warning(f"No documents found in {directory}")
            return documents
        
        for file_path in all_files:
            try:
                if file_path.suffix.lower() == '.md':
                    docs = self._load_markdown(file_path)
                elif file_path.suffix.lower() == '.pdf':
                    docs = self._load_pdf(file_path)
                else:
                    continue
                
                documents.extend(docs)
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")
            
        logger.info(f"Loaded {len(documents)} documents (total pages/files)")
        return documents

    def _load_markdown(self, file_path: Path) -> List[Document]:
        """Load a markdown file."""
        logger.info(f"Loading Markdown: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = self._extract_metadata(content, file_path)
        return [Document(page_content=content, metadata=metadata)]

    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load a PDF file."""
        logger.info(f"Loading PDF: {file_path.name}")
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        
        # Enhance metadata for each page
        for doc in docs:
            doc.metadata.update({
                "source": file_path.name,
                "file_path": str(file_path),
                "type": "pdf"
            })
        return docs

    def process_uploaded_file(self, uploaded_file) -> List[Document]:
        """
        Process a file uploaded through Streamlit.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            List of processed document chunks
        """
        file_name = uploaded_file.name
        logger.info(f"Processing uploaded file: {file_name}")
        
        # Create a temporary file to process
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_name).suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = Path(tmp.name)
            
        try:
            if tmp_path.suffix.lower() == '.md':
                docs = self._load_markdown(tmp_path)
                # Correct the source name from temp to original
                for d in docs: d.metadata["source"] = file_name
            elif tmp_path.suffix.lower() == '.pdf':
                docs = self._load_pdf(tmp_path)
                for d in docs: d.metadata["source"] = file_name
            else:
                raise ValueError(f"Unsupported file type: {tmp_path.suffix}")
                
            # Split into chunks
            chunks = self.split_documents(docs)
            return chunks
        finally:
            # Clean up temp file
            if tmp_path.exists():
                os.remove(tmp_path)
    
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
        global_chunk_count = 0
        
        for doc in documents:
            # Split the document
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk-specific metadata
            for i, chunk in enumerate(chunks):
                # Preserve original metadata
                chunk.metadata.update(doc.metadata)
                
                # Add chunk information
                # Use a global index to prevent duplicate IDs across pages in the same session
                chunk.metadata["chunk_index"] = global_chunk_count
                chunk.metadata["page_chunk_index"] = i
                chunk.metadata["total_page_chunks"] = len(chunks)
                
                # Extract section heading from chunk if available
                section = self._extract_section_heading(chunk.page_content)
                if section:
                    chunk.metadata["section"] = section
                
                all_chunks.append(chunk)
                global_chunk_count += 1
        
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
