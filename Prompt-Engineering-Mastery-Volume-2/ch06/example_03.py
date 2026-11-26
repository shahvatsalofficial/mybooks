class RubricPromptSynthesizer:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def synthesize_system_prompt(self, raw_task_description: str, target_schema_json: str) -> str:
        meta_prompt = (
            "You are an Advanced Generative AI System Prompt Engineer. "
            "Convert the user's high-level task description into an enterprise-grade, production-hardened system prompt.\n\n"
            "You must strictly apply the following 5 Pillars of Enterprise Prompting:\n"
            "1. Persona & Domain Anchor: Establish exact professional seniority and epistemic scope.\n"
            "2. Negative Constraints: State explicitly what the model MUST NOT do (e.g., zero markdown fences, zero speculation).\n"
            "3. Structured Delimiters: Enforce XML blocks (<scratchpad>, <output>) for cognitive separation.\n"
            "4. Edge Case Fallback: Explicitly instruct how to handle empty, conflicting, or malformed inputs.\n"
            "5. Schema Rigidization: Bind the output to the provided JSON Schema.\n\n"
            "Output the final production prompt enclosed in <system_prompt>...</system_prompt> tags."
        )

        user_query = (
            f"Raw Task Description:\n{raw_task_description}\n\n"
            f"Target JSON Schema:\n{target_schema_json}"
        )

        res = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.2,
            system=meta_prompt,
            messages=[{"role": "user", "content": user_query}]
        )

        import re
        match = re.search(r"<system_prompt>(.*?)</system_prompt>", res.content[0].text, re.DOTALL)
        return match.group(1).strip() if match else res.content[0].text.strip()
