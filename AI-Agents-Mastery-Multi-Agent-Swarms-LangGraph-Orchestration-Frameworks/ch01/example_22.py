class SemanticEntityScrubber:
    @staticmethod
    def scrub_confidential_terms(text: str, banned_entities: List[str]) -> str:
        scrubbed = text
        for entity in banned_entities:
            scrubbed = re.sub(re.escape(entity), "[CONFIDENTIAL_REDACTED]", scrubbed, flags=re.IGNORECASE)
        return scrubbed
