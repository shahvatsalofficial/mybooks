class CrewRegressionTester:
    GOLDEN_BENCHMARK = {
        "topic": "Distributed Checkpointing",
        "must_contain": ["Redis", "PostgreSQL", "Redlock", "WAL"],
        "min_word_count": 250
    }

    @classmethod
    def audit_crew_run(cls, output_text: str) -> bool:
        missing = [kw for kw in cls.GOLDEN_BENCHMARK["must_contain"] if kw.lower() not in output_text.lower()]
        word_count = len(output_text.split())
        
        if missing:
            raise AssertionError(f"Regression detected! Output missing mandatory keywords: {missing}")
        if word_count < cls.GOLDEN_BENCHMARK["min_word_count"]:
            raise AssertionError(f"Regression detected! Output word count ({word_count}) below floor ({cls.GOLDEN_BENCHMARK['min_word_count']}).")
            
        print(f"[REGRESSION HARNESS] PASS: All {len(cls.GOLDEN_BENCHMARK['must_contain'])} architectural keywords verified ({word_count} words).")
        return True
