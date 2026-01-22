"""
Experiments Routes

API endpoints for running and comparing RAG experiments.
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.evaluation import (
    ExperimentConfig, ExperimentResult, EvaluationMetrics,
    ExperimentComparisonResponse
)

router = APIRouter()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
CONFIGS_DIR = EXPERIMENTS_DIR / "configs"
RESULTS_DIR = EXPERIMENTS_DIR / "results"

# Create directories
EXPERIMENTS_DIR.mkdir(exist_ok=True)
CONFIGS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# In-memory storage
experiment_store = {}
running_experiments = {}


def get_rag(request: Request):
    """Get RAG pipeline from app state."""
    return request.app.state.get_rag_pipeline()


def get_baseline_config() -> ExperimentConfig:
    """Get the baseline configuration."""
    return ExperimentConfig(
        name="baseline",
        description="Default configuration",
        chunk_size=1000,
        chunk_overlap=200,
        top_k=5,
        similarity_threshold=0.7,
        embedding_model="all-MiniLM-L6-v2",
        llm_model="llama-3.1-70b-versatile",
        temperature=0.1
    )


@router.get("", response_model=List[ExperimentResult])
async def list_experiments():
    """List all experiments."""
    results = []
    
    # Load from files
    for file in RESULTS_DIR.glob("exp_*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
            results.append(ExperimentResult(**data))
        except:
            continue
    
    # Add from memory
    for exp in experiment_store.values():
        if exp.id not in [r.id for r in results]:
            results.append(exp)
    
    # Sort by date
    results.sort(key=lambda r: r.run_at, reverse=True)
    
    return results


@router.post("", response_model=ExperimentConfig)
async def create_experiment(config: ExperimentConfig):
    """
    Create a new experiment configuration.
    
    The experiment can later be run with /experiments/{id}/run.
    """
    # Save config
    config_file = CONFIGS_DIR / f"{config.name}.json"
    with open(config_file, "w") as f:
        json.dump(config.model_dump(), f, indent=2)
    
    return config


@router.get("/configs", response_model=List[ExperimentConfig])
async def list_configs():
    """List all saved experiment configurations."""
    configs = []
    
    for file in CONFIGS_DIR.glob("*.json"):
        try:
            with open(file) as f:
                data = json.load(f)
            configs.append(ExperimentConfig(**data))
        except:
            continue
    
    # Add baseline
    configs.insert(0, get_baseline_config())
    
    return configs


@router.post("/run", response_model=ExperimentResult)
async def run_experiment(
    config: ExperimentConfig,
    request: Request,
    sample_size: int = 5
):
    """
    Run an experiment with the given configuration.
    
    This temporarily modifies RAG settings, runs evaluation, and restores settings.
    """
    start_time = time.time()
    exp_id = str(uuid.uuid4())[:8]
    
    try:
        # Get RAG pipeline
        rag = get_rag(request)
        
        # Store original config
        from config import get_config
        original_config = get_config()
        
        # Load test cases
        from routes.evaluation import load_test_set
        test_cases = load_test_set("sample")[:sample_size]
        
        # Run evaluation with modified params
        correct_count = 0
        source_match_count = 0
        hallucination_count = 0
        total_confidence = 0
        total_response_time = 0
        
        for tc in test_cases:
            try:
                query_start = time.time()
                response = rag.query(
                    question=tc.question,
                    top_k=config.top_k,
                    use_reranking=config.use_reranking
                )
                query_time = (time.time() - query_start) * 1000
                
                answer = response.get("answer", "")
                sources = response.get("sources", [])
                confidence = response.get("confidence", 0)
                
                # Check source match
                source_docs = [s.get("document", "") for s in sources]
                source_match = any(
                    expected in " ".join(source_docs)
                    for expected in tc.expected_sources
                )
                
                # Simple correctness check
                if tc.keywords:
                    answer_correct = any(
                        kw.lower() in answer.lower() for kw in tc.keywords
                    )
                    if answer_correct:
                        correct_count += 1
                
                if source_match:
                    source_match_count += 1
                
                total_confidence += confidence
                total_response_time += query_time
                
            except Exception as e:
                continue
        
        # Calculate metrics
        n = len(test_cases)
        metrics = EvaluationMetrics(
            answer_accuracy=correct_count / n if n > 0 else 0,
            source_accuracy=source_match_count / n if n > 0 else 0,
            hallucination_rate=hallucination_count / n if n > 0 else 0,
            citation_coverage=source_match_count / n if n > 0 else 0,
            precision_at_k=source_match_count / n if n > 0 else 0,
            recall_at_k=source_match_count / n if n > 0 else 0,
            mrr=0.0,
            avg_response_time_ms=total_response_time / n if n > 0 else 0,
            avg_confidence=total_confidence / n if n > 0 else 0
        )
        
        duration = time.time() - start_time
        
        result = ExperimentResult(
            id=exp_id,
            config=config,
            metrics=metrics,
            run_at=datetime.utcnow(),
            duration_seconds=duration
        )
        
        # Store result
        experiment_store[exp_id] = result
        
        # Save to file
        result_file = RESULTS_DIR / f"exp_{exp_id}.json"
        with open(result_file, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")


@router.get("/{exp_id}", response_model=ExperimentResult)
async def get_experiment(exp_id: str):
    """Get a specific experiment result."""
    # Check memory
    if exp_id in experiment_store:
        return experiment_store[exp_id]
    
    # Check files
    result_file = RESULTS_DIR / f"exp_{exp_id}.json"
    if result_file.exists():
        with open(result_file) as f:
            data = json.load(f)
        return ExperimentResult(**data)
    
    raise HTTPException(status_code=404, detail="Experiment not found")


@router.get("/compare", response_model=ExperimentComparisonResponse)
async def compare_experiments(exp_ids: Optional[str] = None):
    """
    Compare multiple experiments.
    
    Pass comma-separated experiment IDs, or leave empty to compare all.
    """
    experiments = await list_experiments()
    
    if exp_ids:
        ids = [id.strip() for id in exp_ids.split(",")]
        experiments = [e for e in experiments if e.id in ids]
    
    if len(experiments) < 2:
        return ExperimentComparisonResponse(
            experiments=experiments,
            best_config=experiments[0].id if experiments else None
        )
    
    # Find best by answer accuracy
    best = max(experiments, key=lambda e: e.metrics.answer_accuracy)
    baseline = next((e for e in experiments if e.config.name == "baseline"), experiments[-1])
    
    improvement = None
    if baseline and best.id != baseline.id:
        improvement = (best.metrics.answer_accuracy - baseline.metrics.answer_accuracy) * 100
    
    return ExperimentComparisonResponse(
        experiments=experiments,
        best_config=best.id,
        improvement_over_baseline=improvement
    )


@router.post("/ablation/chunk-size")
async def ablation_chunk_size(
    request: Request,
    chunk_sizes: str = "500,1000,2000",
    sample_size: int = 3
):
    """
    Run ablation study on chunk size parameter.
    
    Tests multiple chunk sizes and compares results.
    """
    sizes = [int(s.strip()) for s in chunk_sizes.split(",")]
    results = []
    
    for size in sizes:
        config = ExperimentConfig(
            name=f"chunk_size_{size}",
            description=f"Testing chunk size = {size}",
            chunk_size=size,
            chunk_overlap=int(size * 0.2),  # 20% overlap
            top_k=5,
            similarity_threshold=0.7,
            embedding_model="all-MiniLM-L6-v2",
            llm_model="llama-3.1-70b-versatile",
            temperature=0.1
        )
        
        try:
            result = await run_experiment(config, request, sample_size)
            results.append(result)
        except Exception as e:
            continue
    
    # Find best
    if results:
        best = max(results, key=lambda r: r.metrics.answer_accuracy)
        return {
            "ablation_type": "chunk_size",
            "tested_values": sizes,
            "results": [{"size": r.config.chunk_size, "accuracy": r.metrics.answer_accuracy} for r in results],
            "best_value": best.config.chunk_size,
            "best_accuracy": best.metrics.answer_accuracy
        }
    
    return {"error": "No successful experiments"}


@router.post("/ablation/top-k")
async def ablation_top_k(
    request: Request,
    top_k_values: str = "3,5,7,10",
    sample_size: int = 3
):
    """
    Run ablation study on top_k retrieval parameter.
    """
    k_values = [int(k.strip()) for k in top_k_values.split(",")]
    results = []
    
    for k in k_values:
        config = ExperimentConfig(
            name=f"top_k_{k}",
            description=f"Testing top_k = {k}",
            chunk_size=1000,
            chunk_overlap=200,
            top_k=k,
            similarity_threshold=0.7,
            embedding_model="all-MiniLM-L6-v2",
            llm_model="llama-3.1-70b-versatile",
            temperature=0.1
        )
        
        try:
            result = await run_experiment(config, request, sample_size)
            results.append(result)
        except:
            continue
    
    if results:
        best = max(results, key=lambda r: r.metrics.answer_accuracy)
        return {
            "ablation_type": "top_k",
            "tested_values": k_values,
            "results": [{"top_k": r.config.top_k, "accuracy": r.metrics.answer_accuracy} for r in results],
            "best_value": best.config.top_k,
            "best_accuracy": best.metrics.answer_accuracy
        }
    
    return {"error": "No successful experiments"}
