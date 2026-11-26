def filter_blocked_domains(docs: list[SourceDocument], blocklist: set[str]) -> tuple[list[SourceDocument], int]:
    kept = [d for d in docs if d.domain.lower() not in blocklist]
    return kept, len(docs) - len(kept)
