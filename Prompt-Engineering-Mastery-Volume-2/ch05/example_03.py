class EvaluationFirewallError(Exception):
    pass

class GuardedDraftPipeline:
    def __init__(self, client: Anthropic):
        self.client = client
        self.max_retries = 2

    def draft_report(self, raw_data: str, feedback: str = "") -> str:
        prompt = f"Source Data:\n{raw_data}\n\nDraft a formal compliance summary."
        if feedback:
            prompt += f"\n\nPRIOR AUDIT FAILED WITH ERROR:\n{feedback}\nFix these errors strictly."
        
        res = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.2,
            system="You are a Technical Report Generator. Ensure 100% factual accuracy to source data.",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text.strip()

    def audit_draft_firewall(self, raw_data: str, draft: str) -> Tuple[bool, str]:
        """Critic stage: audits draft against source data for hallucinations."""
        eval_prompt = (
            f"Ground Truth Source Data:\n{raw_data}\n\n"
            f"Candidate Draft Summary:\n{draft}\n\n"
            "Audit the draft against ground truth. Are any numbers, dates, or names fabricated or distorted?\n"
            "If fully accurate, output: <verdict>PASS</verdict>\n"
            "If any errors exist, output: <verdict>FAIL: [Explain exact discrepancy]</verdict>"
        )
        res = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            temperature=0.0,
            system="You are an uncompromising zero-tolerance compliance auditor.",
            messages=[{"role": "user", "content": eval_prompt}]
        )
        verdict_text = res.content[0].text.strip()
        if "<verdict>PASS</verdict>" in verdict_text:
            return True, ""
        else:
            return False, verdict_text.replace("<verdict>", "").replace("</verdict>", "")

    def execute_guarded_pipeline(self, raw_data: str) -> str:
        feedback = ""
        for attempt in range(self.max_retries + 1):
            candidate_draft = self.draft_report(raw_data, feedback)
            is_valid, audit_feedback = self.audit_draft_firewall(raw_data, candidate_draft)
            if is_valid:
                return candidate_draft
            feedback = audit_feedback
            print(f"Firewall tripped on attempt {attempt + 1}. Feedback: {feedback}")

        raise EvaluationFirewallError(f"Failed to produce compliant draft after {self.max_retries} retries: {feedback}")
