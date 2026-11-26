"""
Epistemic Abstention Harness: Mandates that an agent evaluate its own
epistemic confidence before answering, enforcing safe abstention on ambiguity.
"""

from typing import Dict, Any, Tuple
import json


class EpistemicAbstentionHarness:
    """Wraps user queries in constitutional abstention envelopes."""

    ABSTENTION_CONSTITUTION = """
<epistemic_mandate version="3.0">
  <rule id="EPI-01">
    You must evaluate your factual confidence across retrieved documents.
    If the provided documents do not contain direct, unambiguous proof to satisfy
    the user's request, you are strictly forbidden from guessing, interpolating,
    or extrapolating.
  </rule>
  <rule id="EPI-02">
    When evidence is insufficient, you MUST output the standardized abstention token:
    <action name="ABSTAIN">
      {
        "status": "INSUFFICIENT_EVIDENCE",
        "missing_information": "[Specify exactly what data is missing]",
        "recommended_action": "ESCALATE_TO_HUMAN"
      }
    </action>
  </rule>
</epistemic_mandate>
"""

    @classmethod
    def wrap_prompt(cls, system_prompt: str, user_query: str, retrieved_context: str) -> str:
        """Injects epistemic mandates and source citations into the execution context."""
        return (
            f"<system_constitution>\n{system_prompt}\n{cls.ABSTENTION_CONSTITUTION}\n</system_constitution>\n\n"
            f"<ground_truth_context>\n{retrieved_context}\n</ground_truth_context>\n\n"
            f"<user_objective>\n{user_query}\n</user_objective>\n"
        )
