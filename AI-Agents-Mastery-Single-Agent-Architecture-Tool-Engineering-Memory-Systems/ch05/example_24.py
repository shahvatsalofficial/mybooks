class DynamicModelRouter:
    def __init__(self, fast_model: ModelEndpoint, large_context_model: ModelEndpoint):
        self.fast_model = fast_model
        self.large_model = large_context_model

    def route_and_execute(self, prompt: str) -> str:
        estimated_tokens = len(prompt) // 4
        if estimated_tokens > 1000:
            return self.large_model.invoke(prompt)
        return self.fast_model.invoke(prompt)
