class ManagedPersonaSession:
    def __init__(self, client: Anthropic, system_prompt: str, reanchor_interval: int = 4):
        self.client = client
        self.system_prompt = system_prompt
        self.reanchor_interval = reanchor_interval
        self.history: List[Dict[str, str]] = []
        self.turn_count = 0

    def send_message(self, user_text: str) -> str:
        self.turn_count += 1
        
        # Check if re-anchoring injection is triggered
        if self.turn_count > 1 and (self.turn_count % self.reanchor_interval == 0):
            reanchor_block = (
                "<system_reminder>\n"
                "MAINTAIN CONSTITUTIONAL PERSONA: You are the Lead Forensic Compliance Auditor. "
                "Maintain uncompromising skepticism. Reject unverified assertions.\n"
                "</system_reminder>\n\n"
            )
            content_payload = reanchor_block + user_text
        else:
            content_payload = user_text

        self.history.append({"role": "user", "content": content_payload})

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.1,
            system=self.system_prompt,
            messages=self.history
        )
        assistant_reply = response.content[0].text
        self.history.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply
