"""
Evaluation Routes

API endpoints for running evaluations and viewing metrics.
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.evaluation import (
    TestCase, TestSetInfo, EvaluationRequest, EvaluationResult,
    EvaluationMetrics, SingleEvaluationResult
)

router = APIRouter()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EVALUATION_DIR = PROJECT_ROOT / "data" / "evaluation"
RESULTS_DIR = EVALUATION_DIR / "results"

# Create directories if needed
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for evaluation results
evaluation_results = {}


def get_rag(request: Request):
    """Get RAG pipeline from app state."""
    return request.app.state.get_rag_pipeline()


def load_test_set(name: str = "default") -> List[TestCase]:
    """Load test set from JSON file."""
    test_file = EVALUATION_DIR / f"{name}_test_set.json"
    
    if not test_file.exists():
        # Try default
        test_file = EVALUATION_DIR / "test_set.json"
    
    if not test_file.exists():
        # Return sample test cases
        return get_sample_test_cases()
    
    with open(test_file) as f:
        data = json.load(f)
    
    return [TestCase(**tc) for tc in data]


def get_sample_test_cases() -> List[TestCase]:
    """Return sample test cases for demo."""
    return [
        TestCase(
            id="tc_001",
            question="What is the minimum credit score for FHA loans?",
            expected_answer="580 for maximum financing, 500-579 requires 10% down payment",
            expected_sources=["credit_scoring_manual.md"],
            category="threshold",
            difficulty="easy",
            keywords=["580", "FHA", "minimum"]
        ),
        TestCase(
            id="tc_002",
            question="What is the maximum DTI ratio for conventional mortgages?",
            expected_answer="43% for qualified mortgages, up to 50% with compensating factors",
            expected_sources=["risk_assessment_guidelines.md"],
            category="threshold",
            difficulty="medium",
            keywords=["43%", "50%", "DTI"]
        ),
        TestCase(
            id="tc_003",
            question="What documentation is required for self-employed borrowers?",
            expected_answer="Two years of tax returns, profit and loss statements, business bank statements",
            expected_sources=["underwriting_policies.md"],
            category="policy",
            difficulty="medium",
            keywords=["tax returns", "self-employed", "documentation"]
        ),
        TestCase(
            id="tc_004",
            question="What is the waiting period after bankruptcy?",
            expected_answer="Chapter 7: 4 years for conventional, 2 years for FHA. Chapter 13: 2 years from discharge",
            expected_sources=["underwriting_policies.md"],
            category="policy",
            difficulty="hard",
            keywords=["bankruptcy", "waiting period", "Chapter 7"]
        ),
        TestCase(
            id="tc_005",
            question="What credit score is needed for the best interest rates?",
            expected_answer="760+ for the best rates, excellent credit tier",
            expected_sources=["credit_scoring_manual.md"],
            category="threshold",
            difficulty="easy",
            keywords=["760", "best rates", "excellent"]
        )
    ]


def check_hallucination(answer: str, sources: List[str], keywords: List[str]) -> bool:
    """Simple hallucination check - looks for numeric claims not in sources."""
    import re
    
    # Extract numbers from answer
    answer_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', answer))
    
    # Extract numbers from sources
    source_text = " ".join(sources)
    source_numbers = set(re.findall(r'\d+(?:\.\d+)?%?', source_text))
    
    # Check if answer has numbers not in sources
    unsupported_numbers = answer_numbers - source_numbers
    
    # Allow small discrepancies (like 0, 1, 2 which might be counts)
    significant_unsupported = [n for n in unsupported_numbers if len(n) > 1]
    
    return len(significant_unsupported) > 0


def calculate_simple_similarity(text1: str, text2: str) -> float:
    """Calculate simple word overlap similarity."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


@router.get("/test-sets", response_model=List[TestSetInfo])
async def list_test_sets():
    """List available test sets."""
    test_sets = []
    
    # Check for JSON files in evaluation directory
    for file in EVALUATION_DIR.glob("*test_set.json"):
        try:
            with open(file) as f:
                data = json.load(f)
            
            name = file.stem.replace("_test_set", "")
            if name == "test":
                name = "default"
            
            # Count categories
            categories = {}
            for tc in data:
                cat = tc.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            test_sets.append(TestSetInfo(
                name=name,
                description=f"Test set from {file.name}",
                total_cases=len(data),
                categories=categories
            ))
        except:
            continue
    
    # Add sample test set if no files found
    if not test_sets:
        sample = get_sample_test_cases()
        categories = {}
        for tc in sample:
            cat = tc.category
            categories[cat] = categories.get(cat, 0) + 1
        
        test_sets.append(TestSetInfo(
            name="sample",
            description="Built-in sample test cases for demonstration",
            total_cases=len(sample),
            categories=categories
        ))
    
    return test_sets


@router.post("/run", response_model=EvaluationResult)
async def run_evaluation(
    request: EvaluationRequest,
    api_request: Request
):
    """
    Run evaluation on a test set.
    
    Returns detailed metrics and individual results.
    """
    rag = get_rag(api_request)
    start_time = time.time()
    
    # Load test cases
    test_cases = load_test_set(request.test_set_name)
    
    if request.sample_size:
        test_cases = test_cases[:request.sample_size]
    
    if not test_cases:
        raise HTTPException(status_code=400, detail="No test cases found")
    
    # Run evaluation
    results = []
    correct_count = 0
    source_match_count = 0
    hallucination_count = 0
    total_confidence = 0
    total_response_time = 0
    
    for tc in test_cases:
        try:
            query_start = time.time()
            response = rag.query(question=tc.question, top_k=5)
            query_time = (time.time() - query_start) * 1000
            
            answer = response.get("answer", "")
            sources = response.get("sources", [])
            confidence = response.get("confidence", 0)
            
            # Extract source documents and content
            source_docs = [s.get("document", "") for s in sources]
            source_texts = [s.get("text", s.get("content", "")) for s in sources]
            
            # Check source match
            source_match = any(
                expected in " ".join(source_docs)
                for expected in tc.expected_sources
            )
            
            # Check hallucination
            has_hallucination = check_hallucination(answer, source_texts, tc.keywords)
            
            # Simple answer correctness (keyword-based for now)
            answer_correct = None
            if tc.expected_answer:
                similarity = calculate_simple_similarity(answer, tc.expected_answer)
                answer_correct = similarity > 0.3 or all(
                    kw.lower() in answer.lower() for kw in tc.keywords
                )
                if answer_correct:
                    correct_count += 1
            
            if source_match:
                source_match_count += 1
            if has_hallucination:
                hallucination_count += 1
            
            total_confidence += confidence
            total_response_time += query_time
            
            results.append(SingleEvaluationResult(
                test_case_id=tc.id,
                question=tc.question,
                expected_answer=tc.expected_answer,
                actual_answer=answer,
                sources_retrieved=source_docs,
                expected_sources=tc.expected_sources,
                answer_correct=answer_correct,
                source_match=source_match,
                has_hallucination=has_hallucination,
                confidence=confidence,
                response_time_ms=query_time
            ))
            
        except Exception as e:
            results.append(SingleEvaluationResult(
                test_case_id=tc.id,
                question=tc.question,
                expected_answer=tc.expected_answer,
                actual_answer=f"Error: {str(e)}",
                sources_retrieved=[],
                expected_sources=tc.expected_sources,
                answer_correct=False,
                source_match=False,
                has_hallucination=False,
                confidence=0,
                response_time_ms=0
            ))
    
    # Calculate metrics
    n = len(test_cases)
    n_with_expected = sum(1 for tc in test_cases if tc.expected_answer)
    
    metrics = EvaluationMetrics(
        answer_accuracy=correct_count / n_with_expected if n_with_expected > 0 else 0,
        source_accuracy=source_match_count / n,
        hallucination_rate=hallucination_count / n,
        citation_coverage=sum(1 for r in results if r.sources_retrieved) / n,
        precision_at_k=source_match_count / n,  # Simplified
        recall_at_k=source_match_count / n,  # Simplified
        mrr=0.0,  # Would need ranked evaluation
        avg_response_time_ms=total_response_time / n,
        avg_confidence=total_confidence / n
    )
    
    # Create result
    eval_id = str(uuid.uuid4())[:8]
    failed_cases = [r.test_case_id for r in results if r.answer_correct is False]
    
    evaluation_result = EvaluationResult(
        id=eval_id,
        test_set_name=request.test_set_name,
        run_at=datetime.utcnow(),
        metrics=metrics,
        results=results,
        failed_cases=failed_cases,
        error_categories={}
    )
    
    # Store result
    evaluation_results[eval_id] = evaluation_result
    
    # Save to file
    result_file = RESULTS_DIR / f"eval_{eval_id}.json"
    with open(result_file, "w") as f:
        json.dump(evaluation_result.model_dump(mode="json"), f, indent=2, default=str)
    
    return evaluation_result


@router.get("/results", response_model=List[EvaluationResult])
async def list_evaluation_results():
    """List all evaluation results."""
    results = []
    
    # Load from files
    for file in RESULTS_DIR.glob("eval_*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
            results.append(EvaluationResult(**data))
        except:
            continue
    
    # Sort by date, newest first
    results.sort(key=lambda r: r.run_at, reverse=True)
    
    return results


@router.get("/results/{eval_id}", response_model=EvaluationResult)
async def get_evaluation_result(eval_id: str):
    """Get a specific evaluation result."""
    # Check memory
    if eval_id in evaluation_results:
        return evaluation_results[eval_id]
    
    # Check files
    result_file = RESULTS_DIR / f"eval_{eval_id}.json"
    if result_file.exists():
        with open(result_file) as f:
            data = json.load(f)
        return EvaluationResult(**data)
    
    raise HTTPException(status_code=404, detail="Evaluation result not found")


@router.get("/metrics/latest")
async def get_latest_metrics():
    """Get metrics from the latest evaluation run."""
    results = await list_evaluation_results()
    
    if not results:
        return {
            "message": "No evaluations run yet",
            "metrics": None
        }
    
    latest = results[0]
    return {
        "eval_id": latest.id,
        "run_at": latest.run_at,
        "metrics": latest.metrics
    }
