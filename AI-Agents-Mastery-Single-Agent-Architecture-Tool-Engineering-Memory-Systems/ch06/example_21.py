class SafeQueryEngineTool:
    def __init__(self, name: str, index: MockDocumentIndex):
        self.name = name
        self.index = index

    def query(self, query_str: str) -> str:
        raw_result = self.index.query(query_str)
        if not raw_result or "No conclusive records" in raw_result:
            return json.dumps({
                "status": "not_found",
                "message": f"Query '{query_str}' yielded zero relevant matches in {self.name}."
            })
        return json.dumps({"status": "success", "result": raw_result})
