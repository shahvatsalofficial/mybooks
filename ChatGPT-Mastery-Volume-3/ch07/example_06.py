# fairness_audit_evaluator.py — Enterprise Statistical Bias Harvester
import pandas as pd
import numpy as np
from typing import Dict, Any

class AlgorithmicFairnessAuditor:
    def __init__(self, dataset_path: str):
        self.df = pd.read_csv(dataset_path)

    def calculate_disparate_impact(
        self,
        prediction_col: str,
        sensitive_col: str,
        favorable_outcome: Any = 1
    ) -> Dict[str, Any]:
        """Calculates Four-Fifths (80%) Rule Disparate Impact Ratio."""
        groups = self.df[sensitive_col].unique()
        selection_rates = {}

        for g in groups:
            sub = self.df[self.df[sensitive_col] == g]
            rate = (sub[prediction_col] == favorable_outcome).mean()
            selection_rates[g] = rate

        max_group = max(selection_rates, key=selection_rates.get)
        max_rate = selection_rates[max_group]

        impact_ratios = {}
        violations = []

        for g, rate in selection_rates.items():
            ratio = rate / max_rate if max_rate > 0 else 1.0
            impact_ratios[g] = round(ratio, 4)
            if ratio < 0.80: # 80% Rule Threshold
                violations.append({
                    "group": g,
                    "selection_rate": round(rate, 4),
                    "benchmark_rate": round(max_rate, 4),
                    "disparate_impact_ratio": round(ratio, 4),
                    "status": "VIOLATION_DETECTED"
                })

        return {
            "highest_selection_group": max_group,
            "benchmark_rate": round(max_rate, 4),
            "selection_rates": selection_rates,
            "disparate_impact_ratios": impact_ratios,
            "adverse_impact_violations": violations,
            "statutory_compliance_pass": len(violations) == 0
        }
