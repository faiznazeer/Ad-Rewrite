"""Evaluation harness with metrics: ROUGE, BLEU, semantic similarity.

This script evaluates the agent by:
1. Using examples.json entries as ground truth (treating them as good rewrites)
2. Running the agent on generic input texts
3. Comparing outputs to ground truth using multiple metrics
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add parent directory to path to import agent modules
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.langgraph_orchestration import run_parallel_rewrites
from agent.platform_agent import _get_embeddings

try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    print("Warning: rouge-score not installed. Install with: pip install rouge-score")

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    BLEU_AVAILABLE = True
except ImportError:
    BLEU_AVAILABLE = False
    print("Warning: nltk not installed. Install with: pip install nltk")

DATA = BASE_DIR / "data"
EXAMPLES = DATA / "examples.json"
OUT_JSON = BASE_DIR / "eval_results.json"


def load_examples(limit: int = 50) -> List[dict]:
    """Load examples from examples.json."""
    with open(EXAMPLES, "r", encoding="utf-8") as f:
        examples = json.load(f)
    return examples[:limit]


def calculate_rouge_score(predicted: str, reference: str) -> Dict[str, float]:
    """Calculate ROUGE-L score (longest common subsequence)."""
    if not ROUGE_AVAILABLE:
        return {"rouge_l": 0.0}
    
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    scores = scorer.score(reference, predicted)
    return {
        "rouge_l": scores["rougeL"].fmeasure,
        "rouge_l_precision": scores["rougeL"].precision,
        "rouge_l_recall": scores["rougeL"].recall,
    }


def calculate_bleu_score(predicted: str, reference: str) -> float:
    """Calculate BLEU score (n-gram precision)."""
    if not BLEU_AVAILABLE:
        return 0.0
    
    # Tokenize
    pred_tokens = predicted.lower().split()
    ref_tokens = reference.lower().split()
    
    # Use smoothing to handle cases where n-grams don't match
    smoothing = SmoothingFunction().method1
    return sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothing)


def calculate_semantic_similarity(predicted: str, reference: str) -> float:
    """Calculate cosine similarity using embeddings."""
    try:
        embeddings = _get_embeddings()
        pred_embedding = embeddings.embed_query(predicted)
        ref_embedding = embeddings.embed_query(reference)
        
        # Cosine similarity
        import numpy as np
        dot_product = np.dot(pred_embedding, ref_embedding)
        norm_pred = np.linalg.norm(pred_embedding)
        norm_ref = np.linalg.norm(ref_embedding)
        
        if norm_pred == 0 or norm_ref == 0:
            return 0.0
        
        return float(dot_product / (norm_pred * norm_ref))
    except Exception as e:
        print(f"Error calculating semantic similarity: {e}")
        return 0.0


def calculate_length_ratio(predicted: str, reference: str) -> float:
    """Calculate length ratio (predicted / reference)."""
    if len(reference) == 0:
        return 0.0
    return len(predicted) / len(reference)


def evaluate_rewrite(
    input_text: str,
    platform: str,
    predicted_output: str,
    ground_truth: str,
) -> Dict[str, float]:
    """Calculate all metrics for a single rewrite."""
    metrics = {}
    
    # ROUGE-L
    rouge_scores = calculate_rouge_score(predicted_output, ground_truth)
    metrics.update(rouge_scores)
    
    # BLEU
    metrics["bleu"] = calculate_bleu_score(predicted_output, ground_truth)
    
    # Semantic similarity
    metrics["semantic_similarity"] = calculate_semantic_similarity(predicted_output, ground_truth)
    
    # Length ratio
    metrics["length_ratio"] = calculate_length_ratio(predicted_output, ground_truth)
    
    return metrics


def create_test_cases(examples: List[dict], num_cases: int = 20) -> List[dict]:
    """Create test cases by pairing generic inputs with example outputs as ground truth.
    
    Strategy: Use examples as ground truth, create simple generic inputs that could
    be rewritten to match the example style.
    """
    test_cases = []
    
    # Group examples by platform
    by_platform = defaultdict(list)
    for ex in examples:
        by_platform[ex["platform"]].append(ex)
    
    # Create test cases
    for platform, platform_examples in by_platform.items():
        if len(test_cases) >= num_cases:
            break
        
        # Take a few examples per platform as ground truth
        for ex in platform_examples[:3]:
            if len(test_cases) >= num_cases:
                break
            
            # Create a generic input that could be rewritten to match the example
            # We'll use a simplified version of the example as input
            generic_input = ex["text"].lower()
            # Remove platform-specific elements to make it more generic
            generic_input = generic_input.replace("!", ".").replace("?", ".")
            
            test_cases.append({
                "input": generic_input,
                "platform": platform,
                "ground_truth": ex["text"],
                "tone": ex.get("tone", ""),
            })
    
    return test_cases[:num_cases]


def evaluate_agent():
    """Run evaluation on test cases and calculate metrics."""
    print("=" * 70)
    print("Evaluating Ad Rewriter Agent")
    print("=" * 70)
    print()
    
    # Load examples
    print("Loading examples...")
    examples = load_examples(50)
    print(f"Loaded {len(examples)} examples")
    
    # Create test cases
    print("\nCreating test cases...")
    test_cases = create_test_cases(examples, num_cases=20)
    print(f"Created {len(test_cases)} test cases")
    
    # Run evaluation
    print("\nRunning agent on test cases...")
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"  [{i}/{len(test_cases)}] Testing {test_case['platform']}...")
        
        try:
            # Run agent
            outputs = run_parallel_rewrites(
                text=test_case["input"],
                target_platforms=[test_case["platform"]],
            )
            
            # Get predicted output
            predicted = ""
            if outputs and isinstance(outputs, list) and len(outputs) > 0:
                predicted = outputs[0].get("rewritten_text", "")
            
            if not predicted:
                print(f"    Warning: No output generated")
                continue
            
            # Calculate metrics
            metrics = evaluate_rewrite(
                input_text=test_case["input"],
                platform=test_case["platform"],
                predicted_output=predicted,
                ground_truth=test_case["ground_truth"],
            )
            
            results.append({
                "test_case": test_case,
                "predicted": predicted,
                "metrics": metrics,
            })
            
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    # Calculate aggregate metrics
    print("\n" + "=" * 70)
    print("Evaluation Results")
    print("=" * 70)
    
    if not results:
        print("No results to evaluate!")
        return
    
    # Aggregate metrics
    aggregate = {
        "rouge_l": [],
        "rouge_l_precision": [],
        "rouge_l_recall": [],
        "bleu": [],
        "semantic_similarity": [],
        "length_ratio": [],
    }
    
    for result in results:
        metrics = result["metrics"]
        for key in aggregate.keys():
            if key in metrics:
                aggregate[key].append(metrics[key])
    
    # Print summary
    print(f"\nTotal test cases: {len(results)}")
    print("\nAverage Metrics:")
    print("-" * 70)
    
    for metric_name, values in aggregate.items():
        if values:
            avg = statistics.mean(values)
            median = statistics.median(values)
            print(f"  {metric_name:20s} | Mean: {avg:.4f} | Median: {median:.4f}")
    
    # Per-platform breakdown
    print("\nPer-Platform Metrics:")
    print("-" * 70)
    
    by_platform = defaultdict(list)
    for result in results:
        platform = result["test_case"]["platform"]
        by_platform[platform].append(result["metrics"])
    
    for platform, metrics_list in by_platform.items():
        if not metrics_list:
            continue
        
        avg_rouge = statistics.mean([m.get("rouge_l", 0) for m in metrics_list])
        avg_semantic = statistics.mean([m.get("semantic_similarity", 0) for m in metrics_list])
        avg_bleu = statistics.mean([m.get("bleu", 0) for m in metrics_list])
        
        print(f"\n  {platform.upper()}:")
        print(f"    ROUGE-L:        {avg_rouge:.4f}")
        print(f"    Semantic Sim:   {avg_semantic:.4f}")
        print(f"    BLEU:           {avg_bleu:.4f}")
        print(f"    Test cases:     {len(metrics_list)}")
    
    # Save detailed results
    output_data = {
        "summary": {
            metric_name: {
                "mean": statistics.mean(values) if values else 0,
                "median": statistics.median(values) if values else 0,
                "std": statistics.stdev(values) if len(values) > 1 else 0,
            }
            for metric_name, values in aggregate.items()
            if values
        },
        "results": results,
    }
    
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {OUT_JSON}")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_agent()

