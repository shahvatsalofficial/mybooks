# tests/test_agent_evaluation_gate.py
"""
CI/CD Quality Gate: Automated Agent Evaluation Test Suite using Pytest & Ragas.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import pytest
import pandas as pd
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset

# Threshold Constants
MIN_FAITHFULNESS = 0.88
MIN_ANSWER_RELEVANCY = 0.82

@pytest.fixture
def golden_benchmark_dataset():
    """
    Loads golden evaluation dataset.
    """
    data = {
        "question": [
            "What is the maximum visibility timeout for an SQS queue?",
            "How does Aurora Global Database manage cross-region replication?"
        ],
        "contexts": [
            [
                "The maximum visibility timeout for an SQS message is 12 hours. By default, it is set to 30 seconds."
            ],
            [
                "AWS Aurora Global Database uses dedicated infrastructure at the storage layer for replication. Replication lag is typically under 1 second."
            ]
        ],
        "answer": [
            "The maximum visibility timeout for an Amazon SQS queue is 12 hours.",
            "Aurora Global Database replicates data at the storage layer with less than 1 second latency."
        ],
        "ground_truth": [
            "The maximum SQS visibility timeout is 12 hours.",
            "Aurora Global Database performs storage-level replication across regions with sub-second RPO."
        ]
    }
    return Dataset.from_dict(data)

def test_agent_performance_quality_gate(golden_benchmark_dataset):
    """
    Executes automated Ragas evaluation suite. Fails pipeline if thresholds are violated.
    """
    print("\n Running CI/CD Agent Evaluation Quality Gate...")
    
    results = evaluate(
        dataset=golden_benchmark_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
    )
    
    df_results = results.to_pandas()
    print("\n--- Evaluation Metric Breakdown ---")
    print(df_results[["faithfulness", "answer_relevancy", "context_precision", "context_recall"]])
    
    avg_faithfulness = df_results["faithfulness"].mean()
    avg_relevancy = df_results["answer_relevancy"].mean()
    
    print(f"\nAverage Faithfulness: {avg_faithfulness:.4f} (Threshold: {MIN_FAITHFULNESS})")
    print(f"Average Relevancy:    {avg_relevancy:.4f} (Threshold: {MIN_ANSWER_RELEVANCY})")
    
    # Enforce quality assertions
    assert avg_faithfulness >= MIN_FAITHFULNESS, f" Quality Gate Blocked: Faithfulness {avg_faithfulness:.4f} < {MIN_FAITHFULNESS}"
    assert avg_relevancy >= MIN_ANSWER_RELEVANCY, f" Quality Gate Blocked: Relevancy {avg_relevancy:.4f} < {MIN_ANSWER_RELEVANCY}"
    
    print("\n All Quality Gate Assertions Passed! Ready for Production Deployment.")
