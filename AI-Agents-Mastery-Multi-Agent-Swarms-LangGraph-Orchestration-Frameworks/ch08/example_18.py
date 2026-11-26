class TrajectoryHeatmapAnalyzer:
    @staticmethod
    def compute_step_percentages(step_durations: Dict[str, float]) -> Dict[str, str]:
        total = sum(step_durations.values())
        return {step: f"{(dur / total) * 100:.1f}%" for step, dur in step_durations.items()}
