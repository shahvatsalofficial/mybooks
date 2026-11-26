import numpy as np

class SyntheticDriftDetector:
    def __init__(self, baseline_turn_distribution: List[int]):
        self.baseline = np.array(baseline_turn_distribution)

    def detect_drift(self, current_turn_samples: List[int], p_value_threshold: float = 0.05) -> bool:
        current = np.array(current_turn_samples)
        # Two-sample KS test approximation
        mean_diff = abs(np.mean(self.baseline) - np.mean(current))
        std_baseline = np.std(self.baseline) or 1.0
        z_score = mean_diff / (std_baseline / np.sqrt(len(current)))

        has_drift = z_score > 2.5
        print(f"[DRIFT DETECTOR] Z-Score: {z_score:.2f} | Drift Detected: {has_drift}")
        return has_drift

baseline = [2, 3, 2, 4, 3, 3, 2, 4, 3, 2]
drifted_samples = [6, 7, 5, 8, 6, 7, 8, 6, 7, 5]
detector = SyntheticDriftDetector(baseline)
is_drift = detector.detect_drift(drifted_samples)
