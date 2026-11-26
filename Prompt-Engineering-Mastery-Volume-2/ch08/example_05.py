import re
from typing import Dict, List, Set, Any
import numpy as np

class RegexFSMTokenizerMasker:
    def __init__(self, vocabulary: Dict[int, str], pattern: str):
        self.vocabulary = vocabulary
        self.pattern = re.compile(pattern)
        self.compiled_fsm: Dict[int, Dict[str, int]] = {}

    def get_legal_token_indices(self, current_prefix: str) -> List[int]:
        """
        Evaluates which vocabulary tokens can be appended to current_prefix
        without violating the target regular expression.
        """
        legal_tokens = []

        for token_id, token_str in self.vocabulary.items():
            candidate_string = current_prefix + token_str
            
            # Check if candidate is a valid prefix of the target pattern
            # Using partial regex matching simulation
            if self._is_valid_prefix(candidate_string):
                legal_tokens.append(token_id)

        return legal_tokens

    def _is_valid_prefix(self, candidate: str) -> bool:
        # Matches prefix against regex pattern
        match = self.pattern.match(candidate)
        if match is not None:
            return True
        # For demonstration: check if any string starting with candidate could match
        # In production engines (Outlines), this uses pre-compiled DFA state tables
        for char in "0123456789abcdefghijklmnopqrstuvwxyz-_\":} ":
            if self.pattern.match(candidate + char):
                return True
        return False

    def apply_mask(self, logits: np.ndarray, current_prefix: str) -> np.ndarray:
        """Masks illegal logits to -infinity."""
        legal_indices = self.get_legal_token_indices(current_prefix)
        masked_logits = np.full_like(logits, -np.inf)
        masked_logits[legal_indices] = logits[legal_indices]
        return masked_logits
