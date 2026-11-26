from typing import List, Dict, Any

class ParentChildHierarchyStore:
    def __init__(self):
        self.parents: Dict[str, str] = {}
        self.children: List[Dict[str, Any]] = []

    def insert_parent_document(self, parent_id: str, full_markdown: str, chunk_size: int = 150) -> None:
        self.parents[parent_id] = full_markdown
        words = full_markdown.split()
        for i in range(0, len(words), chunk_size):
            child_text = " ".join(words[i:i + chunk_size])
            self.children.append({
                "parent_id": parent_id,
                "child_id": f"{parent_id}_c{i//chunk_size}",
                "text": child_text
            })

    def retrieve_parent_context(self, matched_child_id: str) -> str:
        for c in self.children:
            if c["child_id"] == matched_child_id:
                print(f"[HIERARCHY] Matched child '{matched_child_id}'. Hydrating parent '{c['parent_id']}'")
                return self.parents[c["parent_id"]]
        return ""

store = ParentChildHierarchyStore()
doc = "AWS Aurora PostgreSQL Enterprise Runbook. " * 30
store.insert_parent_document("RUNBOOK-PG-01", doc)
parent_ctx = store.retrieve_parent_context("RUNBOOK-PG-01_c0")
print(f"Hydrated Parent Document Length: {len(parent_ctx)} characters")
