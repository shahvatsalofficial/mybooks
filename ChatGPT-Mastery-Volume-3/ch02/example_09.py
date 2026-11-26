# rag_triad_evaluator.py
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)
from datasets import Dataset

class EnterpriseRAGTriadAuditor:
    def __init__(self, golden_dataset_path: str):
        self.metrics = [context_precision, context_recall, faithfulness, answer_relevancy]

    def audit_production_pipeline(self, evaluation_records: list) -> dict:
        """
        evaluation_records expects dicts with:
        - question: str
        - contexts: list[str]
        - answer: str
        - ground_truth: str
        """
        dataset = Dataset.from_list(evaluation_records)
        results = evaluate(dataset, metrics=self.metrics)
        
        # Enforce enterprise quality gates
        assert results["faithfulness"] >= 0.92, f"Faithfulness below SLA: {results['faithfulness']}"
        assert results["answer_relevancy"] >= 0.88, f"Answer Relevancy below SLA: {results['answer_relevancy']}"
        assert results["context_precision"] >= 0.85, f"Context Precision below SLA: {results['context_precision']}"
        
        return results
