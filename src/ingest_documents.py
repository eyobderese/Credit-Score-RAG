#!/usr/bin/env python3
"""
Document Ingestion Script

Processes policy documents and creates the vector database.
"""

import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from document_processor import DocumentProcessor
from vector_store import VectorStore
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main ingestion workflow."""
    print("=" * 60)
    print("Credit Scoring RAG System - Document Ingestion")
    print("=" * 60)
    print()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"  - Data directory: {config.raw_data_dir}")
        print(f"  - Chunk size: {config.chunk_size}")
        print(f"  - Chunk overlap: {config.chunk_overlap}")
        print()
        
        # Initialize document processor
        logger.info("Initializing document processor...")
        processor = DocumentProcessor(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
        print("✓ Document processor initialized")
        print()
        
        # Process documents
        print("Processing documents...")
        print("-" * 60)
        chunks = processor.process_directory(config.raw_data_dir)
        
        if not chunks:
            print("✗ No documents found to process!")
            print(f"  Please add .md files to: {config.raw_data_dir}")
            return 1
        
        print()
        print(f"✓ Processed {len(chunks)} chunks")
        
        # Show summary by source
        sources = {}
        for chunk in chunks:
            source = chunk.metadata.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print("\nDocument breakdown:")
        for source, count in sources.items():
            print(f"  - {source}: {count} chunks")
        
        # Save processed chunks for visibility
        processed_dir = config.processed_data_dir
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        processed_file = processed_dir / "processed_chunks.json"
        with open(processed_file, "w", encoding="utf-8") as f:
            json_chunks = [
                {"content": c.page_content, "metadata": c.metadata}
                for c in chunks
            ]
            json.dump(json_chunks, f, indent=2)
        print(f"\n✓ Saved processed chunks to: {processed_file}")
        print()
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStore(
            persist_directory=config.chroma_persist_dir,
            embedding_model=config.embedding_model
        )
        print("✓ Vector store initialized")
        print()
        
        # Check if collection already has documents
        stats = vector_store.get_collection_stats()
        existing_count = stats.get('total_documents', 0)
        
        if existing_count > 0:
            print(f"⚠ Warning: Collection already contains {existing_count} documents")
            response = input("  Reset and re-ingest? (yes/no): ").strip().lower()
            if response == 'yes':
                vector_store.reset_collection()
                print("✓ Collection reset")
            else:
                print("✗ Ingestion cancelled")
                return 0
        
        # Add documents to vector store
        print("Adding documents to vector store...")
        print("-" * 60)
        vector_store.add_documents(chunks)
        
        print()
        print("=" * 60)
        print("✓ Ingestion Complete!")
        print("=" * 60)
        
        # Show final stats
        final_stats = vector_store.get_collection_stats()
        print(f"\nVector Database Statistics:")
        print(f"  - Total documents: {final_stats['total_documents']}")
        print(f"  - Collection: {final_stats['collection_name']}")
        print(f"  - Embedding model: {final_stats['embedding_model']}")
        print()
        
        print("Next steps:")
        print("  1. Run the Streamlit app: streamlit run src/app.py")
        print("  2. Or use the Python API:")
        print("     from src.rag_pipeline import RAGPipeline")
        print('     rag = RAGPipeline()')
        print('     response = rag.query("your question")')
        print()
        
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
