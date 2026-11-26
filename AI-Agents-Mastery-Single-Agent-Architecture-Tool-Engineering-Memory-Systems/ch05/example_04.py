class ModelEndpoint:
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail

    def invoke(self, prompt: str) -> str:
        if self.should_fail:
            raise ConnectionError(f"Provider timeout on endpoint '{self.name}'.")
        return f"Response from {self.name} for prompt: '{prompt[:30]}...'"

class ResilientModelGateway:
    def __init__(self, primary: ModelEndpoint, backup: ModelEndpoint):
        self.primary = primary
        self.backup = backup

    def invoke_with_fallback(self, prompt: str) -> str:
        try:
            return self.primary.invoke(prompt)
        except ConnectionError as err:
            # Seamless fallback to secondary provider
            print(f"[FALLBACK LOG] {err} -> Switching to {self.backup.name}")
            return self.backup.invoke(prompt)

# Verification
primary_llm = ModelEndpoint(name="Anthropic-Claude-3-5-Sonnet-US-East", should_fail=True)
backup_llm = ModelEndpoint(name="Azure-OpenAI-GPT-4o-EU-West", should_fail=False)

resilient_gateway = ResilientModelGateway(primary=primary_llm, backup=backup_llm)
final_text = resilient_gateway.invoke_with_fallback("Analyze quarterly incident latency metrics.")
print("Final Gateway Result:", final_text)
