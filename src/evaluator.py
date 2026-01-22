"""
Evaluation Module

Measures and reports on RAG system performance.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
import math
import argparse
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_pipeline import RAGPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """Evaluates RAG system performance."""
    
    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize evaluator.
        
        Args:
            rag_pipeline: RAGPipeline instance to evaluate
        """
        self.rag = rag_pipeline
        self.results = []
        self.coverage = {}
    
    def evaluate_query(
        self,
        question: str,
        expected_answer: str = None,
        expected_sources: List[str] = None,
        enable_relevancy: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a single query.
        
        Args:
            question: Test question
            expected_answer: Expected answer (for comparison)
            expected_sources: Expected source documents
            
        Returns:
            Evaluation results dictionary
        """
        start_time = time.time()
        
        try:
            response = self.rag.query(question, validate_answer=True)
            elapsed = time.time() - start_time
            
            result = {
                "question": question,
                "answer": response['answer'],
                "confidence": response.get('confidence', 0),
                "retrieved_count": response['retrieved_count'],
                "response_time": elapsed,
                "retrieval_time": response.get('retrieval_time'),
                "generation_time": response.get('generation_time'),
                "sources": [s['document'] for s in response['sources']],
                "validation": response.get('validation', {}),
                "success": True
            }
            
            # Check if expected sources were retrieved
            if expected_sources:
                expected_set = set(expected_sources)
                found_sources = result['sources']
                result.update(self._compute_retrieval_metrics(found_sources, expected_set))
            else:
                result.update(self._empty_retrieval_metrics())

            # Faithfulness (grounding) metrics from validation
            validation = result.get('validation', {})
            grounded = validation.get('grounded')
            val_conf = validation.get('confidence')
            result['faithfulness_grounded'] = grounded
            result['faithfulness_confidence'] = val_conf

            # Answer relevancy via LLM judge
            if enable_relevancy:
                relevancy = self._judge_relevancy(question, result['answer'])
                result.update(relevancy)
            else:
                result.update({
                    "answer_relevancy_score": None,
                    "answer_relevancy_response": "Skipped (relevancy disabled)"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation error for '{question}': {e}")
            return {
                "question": question,
                "error": str(e),
                "success": False
            }
    
    def evaluate_test_set(
        self,
        test_cases: List[Dict[str, Any]],
        enable_relevancy: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate a set of test cases.
        
        Args:
            test_cases: List of test case dictionaries with 'question', 'expected_answer', etc.
            
        Returns:
            Aggregate evaluation metrics
        """
        logger.info(f"Evaluating {len(test_cases)} test cases")
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Test case {i}/{len(test_cases)}: {test_case['question'][:50]}...")
            
            result = self.evaluate_query(
                question=test_case['question'],
                expected_answer=test_case.get('expected_answer'),
                expected_sources=test_case.get('expected_sources'),
                enable_relevancy=enable_relevancy
            )
            results.append(result)
        
        # Calculate aggregate metrics
        successful = [r for r in results if r['success']]
        
        metrics = {
            "total_tests": len(test_cases),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "success_rate": len(successful) / len(test_cases) if test_cases else 0,
        }
        
        if successful:
            metrics.update({
                "avg_confidence": sum(r['confidence'] for r in successful) / len(successful),
                "avg_response_time": sum(r['response_time'] for r in successful) / len(successful),
                "avg_sources_retrieved": sum(r['retrieved_count'] for r in successful) / len(successful),
                "high_confidence_rate": len([r for r in successful if r['confidence'] >= 80]) / len(successful),
            })

            with_retr_times = [r for r in successful if r.get('retrieval_time') is not None]
            if with_retr_times:
                metrics['avg_retrieval_time'] = sum(r['retrieval_time'] for r in with_retr_times) / len(with_retr_times)
            with_gen_times = [r for r in successful if r.get('generation_time') is not None]
            if with_gen_times:
                metrics['avg_generation_time'] = sum(r['generation_time'] for r in with_gen_times) / len(with_gen_times)

            # Retrieval metrics (only where expected_sources were provided)
            with_retrieval = [r for r in successful if r.get('expected_present')]
            if with_retrieval:
                metrics.update({
                    "avg_precision_at_1": sum(r['precision_at_1'] for r in with_retrieval) / len(with_retrieval),
                    "avg_precision_at_3": sum(r['precision_at_3'] for r in with_retrieval) / len(with_retrieval),
                    "avg_precision_at_5": sum(r['precision_at_5'] for r in with_retrieval) / len(with_retrieval),
                    "avg_recall_at_5": sum(r['recall_at_5'] for r in with_retrieval) / len(with_retrieval),
                    "avg_mrr": sum(r['mrr'] for r in with_retrieval) / len(with_retrieval),
                    "avg_ndcg_at_5": sum(r['ndcg_at_5'] for r in with_retrieval) / len(with_retrieval),
                })

            # Faithfulness and relevancy metrics
            with_faith = [r for r in successful if r.get('faithfulness_confidence') is not None]
            if with_faith:
                metrics['avg_faithfulness_confidence'] = sum(r['faithfulness_confidence'] for r in with_faith) / len(with_faith)
                metrics['faithfulness_grounded_rate'] = len([r for r in with_faith if r.get('faithfulness_grounded')]) / len(with_faith)

            with_rel = [r for r in successful if r.get('answer_relevancy_score') is not None]
            if with_rel:
                metrics['avg_answer_relevancy'] = sum(r['answer_relevancy_score'] for r in with_rel) / len(with_rel)
        
        self.results = results
        self.coverage = self._compute_coverage()
        self.metrics = metrics

        return {
            "metrics": metrics,
            "results": results,
            "coverage": self.coverage
        }

    def evaluate_unlabeled_probes(self, probes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run unlabeled probes to assess retrieval health, groundedness, and refusals."""
        rows = []
        for probe in probes:
            question = probe["question"]
            probe_type = probe.get("type", "normal")

            retrieved = self.rag.retriever.retrieve_with_reranking(question)
            retrieved_count = len(retrieved)
            top_sim = retrieved[0]['similarity'] if retrieved else 0.0
            avg_sim = sum(r['similarity'] for r in retrieved) / len(retrieved) if retrieved else 0.0

            context = self._format_context_from_results(retrieved)
            llm_result = self.rag.llm_handler.generate_with_validation(question, context) if context else {
                "answer": "I don't have information about that in the policy documents.",
                "validation": {"grounded": False, "confidence": 0}
            }

            answer = llm_result.get("answer", "")
            validation = llm_result.get("validation", {})
            grounded = validation.get("grounded")
            faith_conf = validation.get("confidence")

            numeric_fidelity = self._numeric_fidelity(answer, context)
            refusal = self._detect_refusal(answer)

            rows.append({
                "question": question,
                "type": probe_type,
                "retrieved_count": retrieved_count,
                "top_similarity": top_sim,
                "avg_similarity": avg_sim,
                "grounded": grounded,
                "faithfulness_confidence": faith_conf,
                "numeric_fidelity": numeric_fidelity,
                "refusal": refusal,
            })

        return {
            "probes": rows,
            "summary": self._summarize_probes(rows)
        }
    
    def generate_report(self, output_path: str = None) -> str:
        """
        Generate evaluation report.
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Report text
        """
        if not self.results:
            return "No evaluation results available. Run evaluate_test_set() first."
        
        metrics = getattr(self, "metrics", {})
        # Calculate metrics
        successful = [r for r in self.results if r['success']]
        
        report_lines = [
            "=" * 70,
            "RAG SYSTEM EVALUATION REPORT",
            "=" * 70,
            "",
            f"Total Test Cases: {len(self.results)}",
            f"Successful: {len(successful)}",
            f"Failed: {len(self.results) - len(successful)}",
            f"Success Rate: {len(successful)/len(self.results)*100:.1f}%",
            ""
        ]
        
        if successful:
            avg_conf = sum(r['confidence'] for r in successful) / len(successful)
            avg_time = sum(r['response_time'] for r in successful) / len(successful)
            avg_sources = sum(r['retrieved_count'] for r in successful) / len(successful)
            high_conf = len([r for r in successful if r['confidence'] >= 80])
            
            report_lines.extend([
                "PERFORMANCE METRICS:",
                "-" * 70,
                f"Average Confidence: {avg_conf:.1f}%",
                f"High Confidence Rate (≥80%): {high_conf/len(successful)*100:.1f}%",
                f"Average Response Time: {avg_time:.2f} seconds",
                f"Average Sources Retrieved: {avg_sources:.1f}",
                ""
            ])

            if metrics.get('avg_retrieval_time') is not None:
                report_lines.append(f"Avg Retrieval Time: {metrics['avg_retrieval_time']:.2f} seconds")
            if metrics.get('avg_generation_time') is not None:
                report_lines.append(f"Avg Generation Time: {metrics['avg_generation_time']:.2f} seconds")
            report_lines.append("")

            with_retrieval = [r for r in successful if r.get('expected_present')]
            if with_retrieval:
                avg_prec1 = sum(r['precision_at_1'] for r in with_retrieval) / len(with_retrieval)
                avg_prec3 = sum(r['precision_at_3'] for r in with_retrieval) / len(with_retrieval)
                avg_prec5 = sum(r['precision_at_5'] for r in with_retrieval) / len(with_retrieval)
                avg_rec5 = sum(r['recall_at_5'] for r in with_retrieval) / len(with_retrieval)
                avg_mrr = sum(r['mrr'] for r in with_retrieval) / len(with_retrieval)
                avg_ndcg = sum(r['ndcg_at_5'] for r in with_retrieval) / len(with_retrieval)
                report_lines.extend([
                    f"Precision@1/3/5: {avg_prec1:.2f} / {avg_prec3:.2f} / {avg_prec5:.2f}",
                    f"Recall@5: {avg_rec5:.2f}",
                    f"MRR: {avg_mrr:.2f}",
                    f"NDCG@5: {avg_ndcg:.2f}",
                    ""
                ])

            with_faith = [r for r in successful if r.get('faithfulness_confidence') is not None]
            if with_faith:
                avg_faith = sum(r['faithfulness_confidence'] for r in with_faith) / len(with_faith)
                grounded_rate = len([r for r in with_faith if r.get('faithfulness_grounded')]) / len(with_faith)
                report_lines.extend([
                    f"Faithfulness Confidence: {avg_faith:.1f}%",
                    f"Grounded Rate: {grounded_rate*100:.1f}%",
                    ""
                ])

            with_rel = [r for r in successful if r.get('answer_relevancy_score') is not None]
            if with_rel:
                avg_rel = sum(r['answer_relevancy_score'] for r in with_rel) / len(with_rel)
                report_lines.extend([
                    f"Answer Relevancy: {avg_rel:.1f}%",
                    ""
                ])
        
        # Coverage section
        if self.coverage:
            report_lines.extend([
                "COVERAGE CHECKS:",
                "-" * 70,
                f"Raw markdown files: {self.coverage.get('raw_markdown_files')}",
                f"Processed chunks file: {self.coverage.get('processed_chunks')}",
                f"Vector store documents: {self.coverage.get('vector_total_documents')} (collection: {self.coverage.get('vector_collection')})",
                ""
            ])

        # Individual results
        report_lines.extend([
            "DETAILED RESULTS:",
            "-" * 70,
            ""
        ])
        
        for i, result in enumerate(self.results, 1):
            if result['success']:
                report_lines.extend([
                    f"Test Case {i}:",
                    f"  Question: {result['question']}",
                    f"  Confidence: {result['confidence']}%",
                    f"  Sources: {', '.join(result['sources'])}",
                    f"  Response Time: {result['response_time']:.2f}s",
                    f"  Precision@1/3/5: {result['precision_at_1']:.2f}/{result['precision_at_3']:.2f}/{result['precision_at_5']:.2f}",
                    f"  Recall@5: {result['recall_at_5']:.2f} | MRR: {result['mrr']:.2f} | NDCG@5: {result['ndcg_at_5']:.2f}",
                    f"  Faithfulness: {result.get('faithfulness_confidence', 'n/a')} (grounded={result.get('faithfulness_grounded')})",
                    f"  Answer Relevancy: {result.get('answer_relevancy_score', 'n/a')}",
                    ""
                ])
            else:
                report_lines.extend([
                    f"Test Case {i}: FAILED",
                    f"  Question: {result['question']}",
                    f"  Error: {result.get('error', 'Unknown')}",
                    ""
                ])
        
        report = "\n".join(report_lines)
        
        # Save to file if requested
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to: {output_path}")
        
        return report

    # --- Metrics helpers ---
    def _compute_retrieval_metrics(self, retrieved: List[str], expected_set: set) -> Dict[str, Any]:
        """Compute retrieval metrics given ordered retrieved docs and expected set."""
        metrics = {
            "expected_present": bool(expected_set),
            "precision_at_1": self._precision_at_k(retrieved, expected_set, 1),
            "precision_at_3": self._precision_at_k(retrieved, expected_set, 3),
            "precision_at_5": self._precision_at_k(retrieved, expected_set, 5),
            "recall_at_5": self._recall_at_k(retrieved, expected_set, 5),
            "mrr": self._mrr(retrieved, expected_set),
            "ndcg_at_5": self._ndcg_at_k(retrieved, expected_set, 5),
        }
        # Legacy source recall for compatibility
        metrics["source_recall"] = metrics["recall_at_5"]
        return metrics

    def _empty_retrieval_metrics(self) -> Dict[str, Any]:
        return {
            "expected_present": False,
            "precision_at_1": 0.0,
            "precision_at_3": 0.0,
            "precision_at_5": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "ndcg_at_5": 0.0,
            "source_recall": 0.0,
        }

    @staticmethod
    def _precision_at_k(retrieved: List[str], expected: set, k: int) -> float:
        if not expected:
            return 0.0
        if not retrieved:
            return 0.0
        cutoff = retrieved[:k]
        hits = sum(1 for doc in cutoff if doc in expected)
        return hits / min(k, len(retrieved))

    @staticmethod
    def _recall_at_k(retrieved: List[str], expected: set, k: int) -> float:
        if not expected:
            return 0.0
        cutoff = retrieved[:k]
        hits = sum(1 for doc in cutoff if doc in expected)
        return hits / len(expected)

    @staticmethod
    def _mrr(retrieved: List[str], expected: set) -> float:
        for idx, doc in enumerate(retrieved):
            if doc in expected:
                return 1.0 / (idx + 1)
        return 0.0

    @staticmethod
    def _ndcg_at_k(retrieved: List[str], expected: set, k: int) -> float:
        if not expected:
            return 0.0
        dcg = 0.0
        for idx, doc in enumerate(retrieved[:k]):
            rel = 1.0 if doc in expected else 0.0
            dcg += rel / math.log2(idx + 2)
        ideal_hits = min(len(expected), k)
        idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
        return dcg / idcg if idcg > 0 else 0.0

    def _judge_relevancy(self, question: str, answer: str) -> Dict[str, Any]:
        """Use LLM judge to score answer relevancy to the question."""
        if not answer:
            return {"answer_relevancy_score": None, "answer_relevancy_response": "No answer provided"}
        llm = getattr(self.rag, "llm_handler", None)
        if llm is None:
            return {"answer_relevancy_score": None, "answer_relevancy_response": "LLM handler unavailable"}

        prompt = f"""You are a strict relevance grader.

Return ONLY compact JSON. No prose. Schema: {{"score": <0-100 integer>, "rationale": "<short>"}}

QUESTION: {question}
ANSWER: {answer}
"""
        try:
            response = llm.client.chat.completions.create(
                model=llm.model,
                messages=[
                    {"role": "system", "content": "You output only JSON for relevance grading."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=200
            )
            raw = response.choices[0].message.content
            try:
                parsed = json.loads(raw)
                score = parsed.get("score") if isinstance(parsed, dict) else None
            except Exception:
                import re
                score_match = re.search(r"score['\s:]+(\d{1,3})", raw, re.IGNORECASE)
                score = int(score_match.group(1)) if score_match else None
            if score is None:
                logger.warning(f"Relevancy judge returned unparsable response: {raw}")
            return {
                "answer_relevancy_score": score,
                "answer_relevancy_response": raw
            }
        except Exception as e:
            logger.warning(f"Relevancy judging failed: {e}")
            return {
                "answer_relevancy_score": None,
                "answer_relevancy_response": f"Error: {e}"
            }

    def _format_context_from_results(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieved results into context string (mirrors pipeline formatting)."""
        if not results:
            return ""
        parts = []
        for i, doc in enumerate(results, 1):
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            section = metadata.get('section', 'General')
            parts.append(
                f"[Context {i}] Source: {source} | Section: {section}\n{doc.get('text', '')}"
            )
        return "\n\n---\n\n".join(parts)

    @staticmethod
    def _detect_refusal(answer: str) -> bool:
        if not answer:
            return False
        lower = answer.lower()
        phrases = [
            "i don't have information",
            "not in the policy documents",
            "no information available",
            "i don't know"
        ]
        return any(p in lower for p in phrases)

    @staticmethod
    def _extract_numbers(text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"\d+(?:\.\d+)?", text)

    def _numeric_fidelity(self, answer: str, context: str) -> Optional[float]:
        """Return fraction of numbers in answer that also appear in context."""
        nums_ans = self._extract_numbers(answer)
        if not nums_ans:
            return None
        nums_ctx = set(self._extract_numbers(context))
        if not nums_ctx:
            return 0.0
        hits = sum(1 for n in nums_ans if n in nums_ctx)
        return hits / len(nums_ans)

    @staticmethod
    def _summarize_probes(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {}
        hit_rate = len([r for r in rows if r['retrieved_count'] > 0]) / len(rows)
        grounded_rows = [r for r in rows if r.get('grounded') is not None]
        grounded_rate = len([r for r in grounded_rows if r.get('grounded')]) / len(grounded_rows) if grounded_rows else 0
        avg_faith = sum(r.get('faithfulness_confidence', 0) for r in grounded_rows) / len(grounded_rows) if grounded_rows else 0
        avg_top_sim = sum(r['top_similarity'] for r in rows) / len(rows)
        avg_sim = sum(r['avg_similarity'] for r in rows) / len(rows)
        numeric_rows = [r for r in rows if r.get('numeric_fidelity') is not None]
        avg_numeric = sum(r['numeric_fidelity'] for r in numeric_rows) / len(numeric_rows) if numeric_rows else None
        unanswerable = [r for r in rows if r.get('type') == 'unanswerable']
        refusal_rate = len([r for r in unanswerable if r.get('refusal')]) / len(unanswerable) if unanswerable else None
        return {
            "hit_rate": hit_rate,
            "grounded_rate": grounded_rate,
            "avg_faithfulness_confidence": avg_faith,
            "avg_top_similarity": avg_top_sim,
            "avg_similarity": avg_sim,
            "avg_numeric_fidelity": avg_numeric,
            "refusal_rate_unanswerable": refusal_rate,
        }

    def _compute_coverage(self) -> Dict[str, Any]:
        """Check ingestion coverage: raw files, processed chunks, vector store count."""
        cfg = self.rag.config
        raw_dir = cfg.raw_data_dir
        raw_files = list(raw_dir.glob("*.md")) if raw_dir.exists() else []
        raw_count = len(raw_files)
        processed_file = cfg.processed_data_dir / "processed_chunks.json"
        processed_chunks = None
        if processed_file.exists():
            try:
                with open(processed_file, "r", encoding="utf-8") as f:
                    processed_chunks = len(json.load(f))
            except Exception as e:
                logger.warning(f"Could not read processed chunks: {e}")
        vector_stats = self.rag.vector_store.get_collection_stats()
        return {
            "raw_markdown_files": raw_count,
            "vector_total_documents": vector_stats.get("total_documents"),
            "processed_chunks": processed_chunks,
            "vector_collection": vector_stats.get("collection_name"),
            "embedding_model": vector_stats.get("embedding_model")
        }


# Sample test cases
SAMPLE_TEST_CASES = [
    {
        "question": "What is the minimum credit score for FHA loans?",
        "expected_sources": ["credit_scoring_manual.md"],
    },
    {
        "question": "What are the DTI limits for conventional mortgages?",
        "expected_sources": ["risk_assessment_guidelines.md"],
    },
    {
        "question": "What documentation is required for self-employed borrowers?",
        "expected_sources": ["underwriting_policies.md", "risk_assessment_guidelines.md"],
    },
    {
        "question": "What are the reserve requirements for investment properties?",
        "expected_sources": ["risk_assessment_guidelines.md"],
    },
    {
        "question": "What is the maximum LTV for jumbo loans?",
        "expected_sources": ["risk_assessment_guidelines.md"],
    }
]


def main():
    """Run evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline")
    parser.add_argument(
        "--no-relevancy",
        action="store_false",
        dest="enable_relevancy",
        help="Skip LLM-based answer relevancy grading to save costs/time"
    )
    parser.add_argument(
        "--run-unlabeled",
        action="store_true",
        help="Run unlabeled probe suite (retrieval health, groundedness, refusals, numeric fidelity)"
    )
    args = parser.parse_args()

    print("Initializing RAG system...")
    rag = RAGPipeline()
    
    print("Creating evaluator...")
    evaluator = RAGEvaluator(rag)
    
    print(f"\nRunning evaluation on {len(SAMPLE_TEST_CASES)} test cases...")
    print("=" * 70)
    
    evaluation = evaluator.evaluate_test_set(SAMPLE_TEST_CASES, enable_relevancy=args.enable_relevancy)
    
    print("\n" + evaluator.generate_report())
    
    # Save results as JSON
    project_root = Path(__file__).parent.parent
    results_path = project_root / "evaluation_results.json"
    
    if args.run_unlabeled:
        print("\nRunning unlabeled probes...")
        probes = [
            {"question": "What is the minimum credit score for FHA loans?"},
            {"question": "DTI limits for conventional mortgages?"},
            {"question": "Max LTV for investment properties with 700 score?"},
            {"question": "Wait times after bankruptcy?"},
            {"question": "What is the capital city of France?", "type": "unanswerable"},
            {"question": "Who won the NBA finals?", "type": "unanswerable"},
        ]
        unlabeled = evaluator.evaluate_unlabeled_probes(probes)
        evaluation["unlabeled"] = unlabeled
        summary = unlabeled.get("summary", {})
        print("\nUnlabeled Probe Summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")

    with open(results_path, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_path}")


if __name__ == "__main__":
    main()
