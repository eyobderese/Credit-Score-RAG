"""
Evaluation Module

Measures and reports on RAG system performance.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import json
import time

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
    
    def evaluate_query(
        self,
        question: str,
        expected_answer: str = None,
        expected_sources: List[str] = None
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
                "sources": [s['document'] for s in response['sources']],
                "validation": response.get('validation', {}),
                "success": True
            }
            
            # Check if expected sources were retrieved
            if expected_sources:
                found_sources = set(result['sources'])
                expected_set = set(expected_sources)
                source_recall = len(found_sources & expected_set) / len(expected_set) if expected_set else 0
                result['source_recall'] = source_recall
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation error for '{question}': {e}")
            return {
                "question": question,
                "error": str(e),
                "success": False
            }
    
    def evaluate_test_set(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
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
                expected_sources=test_case.get('expected_sources')
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
            
            # Source recall (if available)
            with_source_recall = [r for r in successful if 'source_recall' in r]
            if with_source_recall:
                metrics['avg_source_recall'] = sum(r['source_recall'] for r in with_source_recall) / len(with_source_recall)
        
        self.results = results
        
        return {
            "metrics": metrics,
            "results": results
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
            
            # Source recall if available
            with_recall = [r for r in successful if 'source_recall' in r]
            if with_recall:
                avg_recall = sum(r['source_recall'] for r in with_recall) / len(with_recall)
                report_lines.extend([
                    f"Average Source Recall: {avg_recall*100:.1f}%",
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
    print("Initializing RAG system...")
    rag = RAGPipeline()
    
    print("Creating evaluator...")
    evaluator = RAGEvaluator(rag)
    
    print(f"\nRunning evaluation on {len(SAMPLE_TEST_CASES)} test cases...")
    print("=" * 70)
    
    evaluation = evaluator.evaluate_test_set(SAMPLE_TEST_CASES)
    
    print("\n" + evaluator.generate_report())
    
    # Save results as JSON
    project_root = Path(__file__).parent.parent
    results_path = project_root / "evaluation_results.json"
    
    with open(results_path, 'w') as f:
        json.dump(evaluation, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_path}")


if __name__ == "__main__":
    main()
