"""
Pydantic models for evaluation-related requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class QuestionCategory(str, Enum):
    """Categories of test questions."""
    THRESHOLD = "threshold"
    POLICY = "policy"
    DEFINITION = "definition"
    EDGE_CASE = "edge_case"
    MULTI_HOP = "multi_hop"


class QuestionDifficulty(str, Enum):
    """Difficulty levels for test questions."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestCase(BaseModel):
    """A single test case for evaluation."""
    id: str = Field(..., description="Unique test case ID")
    question: str = Field(..., description="The test question")
    expected_answer: Optional[str] = Field(None, description="Expected answer (ground truth)")
    expected_sources: List[str] = Field(default_factory=list, description="Expected source documents")
    category: QuestionCategory = Field(QuestionCategory.POLICY)
    difficulty: QuestionDifficulty = Field(QuestionDifficulty.MEDIUM)
    keywords: List[str] = Field(default_factory=list, description="Keywords that should appear")


class TestSetInfo(BaseModel):
    """Information about a test set."""
    name: str = Field(...)
    description: Optional[str] = None
    total_cases: int = Field(..., ge=0)
    categories: Dict[str, int] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationRequest(BaseModel):
    """Request to run an evaluation."""
    test_set_name: str = Field("default", description="Name of test set to use")
    sample_size: Optional[int] = Field(None, description="Limit to N samples (None = all)")
    include_sources: bool = Field(True, description="Include source analysis")


class SingleEvaluationResult(BaseModel):
    """Result for a single test case."""
    test_case_id: str
    question: str
    expected_answer: Optional[str]
    actual_answer: str
    sources_retrieved: List[str]
    expected_sources: List[str]
    
    # Metrics
    answer_correct: Optional[bool] = None
    source_match: bool = False
    has_hallucination: bool = False
    confidence: int = 0
    response_time_ms: float = 0
    
    # Scores
    bert_score: Optional[float] = None
    rouge_score: Optional[float] = None


class EvaluationMetrics(BaseModel):
    """Aggregate evaluation metrics."""
    # Accuracy
    answer_accuracy: float = Field(..., ge=0, le=1, description="% correct answers")
    source_accuracy: float = Field(..., ge=0, le=1, description="% correct source attribution")
    
    # Quality
    hallucination_rate: float = Field(..., ge=0, le=1, description="% with hallucinations")
    citation_coverage: float = Field(..., ge=0, le=1, description="% with valid citations")
    
    # Retrieval
    precision_at_k: float = Field(..., ge=0, le=1)
    recall_at_k: float = Field(..., ge=0, le=1)
    mrr: float = Field(..., ge=0, le=1, description="Mean Reciprocal Rank")
    
    # Performance
    avg_response_time_ms: float = Field(..., ge=0)
    avg_confidence: float = Field(..., ge=0, le=100)
    
    # BERTScore (if computed)
    avg_bert_score: Optional[float] = None


class EvaluationResult(BaseModel):
    """Complete evaluation result."""
    id: str = Field(...)
    test_set_name: str
    run_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Summary metrics
    metrics: EvaluationMetrics
    
    # Individual results
    results: List[SingleEvaluationResult] = Field(default_factory=list)
    
    # Error analysis
    failed_cases: List[str] = Field(default_factory=list, description="IDs of failed cases")
    error_categories: Dict[str, int] = Field(default_factory=dict)


class ExperimentConfig(BaseModel):
    """Configuration for an experiment."""
    name: str = Field(...)
    description: Optional[str] = None
    
    # Chunking params
    chunk_size: int = Field(1000, ge=100, le=5000)
    chunk_overlap: int = Field(200, ge=0, le=1000)
    
    # Retrieval params
    top_k: int = Field(5, ge=1, le=20)
    similarity_threshold: float = Field(0.7, ge=0, le=1)
    
    # Model params
    embedding_model: str = Field("all-MiniLM-L6-v2")
    llm_model: str = Field("llama-3.1-70b-versatile")
    temperature: float = Field(0.1, ge=0, le=2)
    
    # Advanced
    use_reranking: bool = Field(True)
    use_hybrid_search: bool = Field(False)


class ExperimentResult(BaseModel):
    """Result of running an experiment."""
    id: str = Field(...)
    config: ExperimentConfig
    metrics: EvaluationMetrics
    run_at: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: float = Field(...)


class ExperimentComparisonResponse(BaseModel):
    """Response for comparing experiments."""
    experiments: List[ExperimentResult]
    best_config: Optional[str] = Field(None, description="ID of best performing config")
    improvement_over_baseline: Optional[float] = None
