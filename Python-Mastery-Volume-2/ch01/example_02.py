class FragileService:
    def process(self, data: bytes) -> None:
        pass

    def process(self, text: str) -> None:  # Silently overwrites the bytes handler!
        pass
