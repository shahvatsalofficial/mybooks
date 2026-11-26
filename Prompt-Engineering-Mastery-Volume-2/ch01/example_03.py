from typing import List, Dict
import anthropic

class CoTExemplar:
    def __init__(self, query: str, scratchpad: str, final_answer: str):
        self.query = query
        self.scratchpad = scratchpad
        self.final_answer = final_answer

    def format_for_prompt(self) -> str:
        return (
            f"<example>\n"
            f"<input>{self.query}</input>\n"
            f"<scratchpad>\n{self.scratchpad}\n</scratchpad>\n"
            f"<output>{self.final_answer}</output>\n"
            f"</example>"
        )

class DynamicFewShotCoTEngine:
    def __init__(self, exemplars: List[CoTExemplar]):
        self.exemplars = exemplars

    def build_system_context(self) -> str:
        exemplar_blocks = "\n\n".join([e.format_for_prompt() for e in self.exemplars])
        return (
            "You are a Logic and Constraint Verification Engine. "
            "Examine the provided examples to understand the expected depth of step-by-step scratchpad derivation. "
            "You must follow the exact structure demonstrated in the examples:\n\n"
            f"{exemplar_blocks}\n\n"
            "When answering the user query, output <scratchpad> followed by <output>."
        )

    def generate_prompt(self, target_query: str) -> str:
        return f"<input>{target_query}</input>"

# Instantiating curated exemplars
exemplars = [
    CoTExemplar(
        query="Server cluster A has 16 nodes at 85% load. Server cluster B has 8 nodes at 40% load. Can we migrate 4 nodes of load from A to B?",
        scratchpad=(
            "1. Calculate total current load units on Cluster A: 16 nodes * 0.85 = 13.6 load units.\n"
            "2. Load of 4 nodes on Cluster A: 4 * 0.85 = 3.4 load units.\n"
            "3. Calculate available capacity on Cluster B: 8 nodes * (1.0 - 0.40) = 8 * 0.60 = 4.8 load units.\n"
            "4. Compare migration demand to available capacity: Demand (3.4) <= Available (4.8).\n"
            "5. Remaining headroom on Cluster B after migration: 4.8 - 3.4 = 1.4 load units.\n"
            "6. Conclude: Migration is mathematically feasible without exceeding cluster capacity."
        ),
        final_answer="FEASIBLE: Cluster B can absorb the 3.4 load units with 1.4 units of remaining capacity."
    )
]

dispatcher = DynamicFewShotCoTEngine(exemplars)
