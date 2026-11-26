class EvaluationDatasetGenerator:
    @staticmethod
    def create_synthetic_test_case(domain: str, difficulty: str) -> Dict[str, Any]:
        return {
            "case_id": str(uuid.uuid4()),
            "domain": domain,
            "difficulty": difficulty,
            "prompt": f"Stress test prompt for {domain} under {difficulty} constraints."
        }
