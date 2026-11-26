class ContentBasedRouter:
    def __init__(self, routing_rules: List[Tuple[str, str]]):
        self.rules = routing_rules # (regex_pattern, target_queue)

    def route_payload(self, text_content: str) -> str:
        for pattern, queue in self.rules:
            if re.search(pattern, text_content, re.IGNORECASE):
                print(f"[CONTENT ROUTER] Matched '{pattern}' -> Routing to queue '{queue}'")
                return queue
        return "default_unmatched_queue"
