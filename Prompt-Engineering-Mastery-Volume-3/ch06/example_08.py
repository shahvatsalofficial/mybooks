# remediation_clinical_firewall.py
# Production architectural fix: Enforces zero-tolerance numerical factuality verification.

import re
from typing import List, Tuple


class ClinicalNumericalGroundingFirewall:
    """Enforces 100% exact numerical match between clinical protocols and source monographs."""

    DOSAGE_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*(mg/kg|mg|mcg|g|ml)", re.IGNORECASE)

    def audit_numerical_grounding(
        self,
        draft_protocol: str,
        source_monograph_text: str
    ) -> Tuple[bool, List[str]]:
        """Verifies that every numerical dosage in the protocol appears in source text."""
        errors = []
        generated_dosages = self.DOSAGE_REGEX.findall(draft_protocol)

        for value_str, unit in generated_dosages:
            exact_phrase = f"{value_str} {unit}".lower()
            compact_phrase = f"{value_str}{unit}".lower()

            if (exact_phrase not in source_monograph_text.lower()) and \
               (compact_phrase not in source_monograph_text.lower()):
                errors.append(
                    f"CRITICAL_NUMERICAL_HALLUCINATION: Generated dosage '{exact_phrase}' "
                    f"does not exist in source monograph text. Immediate abort required."
                )

        return len(errors) == 0, errors
