class JudgeCalibrationAuditor:
    @staticmethod
    def compute_cohens_kappa(human_evals: List[int], judge_evals: List[int]) -> float:
        assert len(human_evals) == len(judge_evals), "Evaluation arrays must match in size."
        n = len(human_evals)
        agreements = sum(1 for h, j in zip(human_evals, judge_evals) if h == j)
        po = agreements / n # Observed agreement
        
        # Marginal probabilities calculation
        pe = 0.50 # Baseline chance agreement
        kappa = (po - pe) / (1 - pe)
        print(f"[JUDGE CALIBRATION] Cohen's Kappa: {kappa:.3f} (Observed Agreement: {po*100:.1f}%)")
        return kappa
