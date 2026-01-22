"""
Streamlit Application

Interactive web interface for the Credit Scoring RAG system.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_pipeline import RAGPipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="Credit Policy Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_rag():
    """Initialize RAG pipeline (cached)."""
    try:
        return RAGPipeline()
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        st.stop()


def get_confidence_class(confidence: int) -> str:
    """Get CSS class based on confidence score."""
    if confidence >= 80:
        return "confidence-high"
    elif confidence >= 60:
        return "confidence-medium"
    else:
        return "confidence-low"


def format_confidence(confidence: int) -> str:
    """Format confidence score with color."""
    css_class = get_confidence_class(confidence)
    return f'<span class="{css_class}">{confidence}%</span>'


def main():
    """Main application."""
    
    # Header
    st.markdown('<div class="main-header">🏦 Credit Policy Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Ask questions about credit scoring, underwriting policies, and risk assessment guidelines</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Initialize RAG
        rag = initialize_rag()
        
        # Get system stats
        stats = rag.get_stats()
        
        st.subheader("System Information")
        st.metric("Indexed Documents", stats['total_documents'])
        st.metric("LLM Model", stats['llm_model'])
        
        st.divider()
        
        # Query settings
        st.subheader("Query Settings")
        
        top_k = st.slider(
            "Number of sources to retrieve",
            min_value=1,
            max_value=10,
            value=stats['top_k'],
            help="How many relevant document chunks to retrieve"
        )
        
        use_reranking = st.checkbox(
            "Use reranking",
            value=True,
            help="Rerank results for better relevance"
        )
        
        validate_answer = st.checkbox(
            "Validate answers",
            value=False,
            help="Use LLM to validate answer grounding (slower)"
        )
        
        st.divider()
        
        # Debug mode
        debug_mode = st.checkbox("Debug mode", value=False)
        
        st.divider()
        
        # Example queries
        st.subheader("💡 Example Questions")
        examples = [
            "What is the minimum credit score for FHA loans?",
            "What are the DTI limits for conventional mortgages?",
            "What documentation is required for self-employed borrowers?",
            "What are the reserve requirements for investment properties?",
            "What are the waiting periods after bankruptcy?",
            "What is the maximum LTV for a primary residence with a 650 credit score?"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{hash(example)}"):
                st.session_state.query = example
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Query input
        query = st.text_area(
            "Ask your question:",
            value=st.session_state.get('query', ''),
            height=100,
            placeholder="e.g., What is the minimum credit score for conventional loans?"
        )
        
        submit_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    with col2:
        st.info("""
        **Tips for better results:**
        - Be specific in your questions
        - Mention specific loan types or policies
        - Ask about numerical thresholds
        - Reference specific borrower scenarios
        """)
    
    # Process query
    if submit_button and query:
        with st.spinner("Searching policy documents..."):
            try:
                # Query the RAG system
                response = rag.query(
                    question=query,
                    top_k=top_k,
                    use_reranking=use_reranking,
                    validate_answer=validate_answer
                )
                
                # Display answer
                st.markdown("---")
                st.subheader("📋 Answer")
                
                # Show confidence
                confidence = response.get('confidence', 0)
                st. markdown(
                    f"**Confidence:** {format_confidence(confidence)}",
                    unsafe_allow_html=True
                )
                
                # Show answer
                st.markdown(response['answer'])
                
                # Show metadata
                col_meta1, col_meta2, col_meta3 = st.columns(3)
                with col_meta1:
                    st.metric("Sources Used", response['retrieved_count'])
                with col_meta2:
                    st.metric("Response Time", f"{response.get('response_time', 0):.2f}s")
                with col_meta3:
                    st.metric("Tokens Used", response.get('tokens_used', 0))
                
                # Display sources
                if response['sources']:
                    st.markdown("---")
                    st.subheader("📚 Sources")
                    
                    for i, source in enumerate(response['sources'], 1):
                        with st.expander(
                            f"Source {i}: {source['document']} - {source['section']} "
                            f"(Similarity: {source['similarity']:.2%})"
                        ):
                            st.markdown(f"**Document:** {source['document']}")
                            st.markdown(f"**Section:** {source['section']}")
                            st.markdown(f"**Similarity Score:** {source['similarity']:.3f}")
                            
                            if 'version' in source:
                                st.markdown(f"**Version:** {source['version']}")
                            if 'effective_date' in source:
                                st.markdown(f"**Effective Date:** {source['effective_date']}")
                            
                            st.markdown("**Content:**")
                            st.text_area(
                                "Source text",
                                value=source['text_preview'],
                                height=150,
                                key=f"source_{i}",
                                label_visibility="collapsed"
                            )
                
                # Debug information
                if debug_mode:
                    st.markdown("---")
                    st.subheader("🔧 Debug Information")
                    
                    with st.expander("Full Response Object"):
                        st.json(response)
                    
                    if validate_answer and 'validation' in response:
                        with st.expander("Answer Validation"):
                            st.json(response['validation'])
                
            except Exception as e:
                st.error(f"Error processing query: {e}")
                logger.error(f"Query error: {e}", exc_info=True)
    
    elif submit_button:
        st.warning("Please enter a question first.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        Credit Policy Assistant v1.0 | Powered by Groq & ChromaDB
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
