class DocumentGraphNode:
    def __init__(self, node_id: str, text: str, parent_id: Optional[str] = None):
        self.node_id = node_id
        self.text = text
        self.parent_id = parent_id
        self.child_ids: List[str] = []

class DocumentGraphIndex:
    def __init__(self):
        self.nodes: Dict[str, DocumentGraphNode] = {}

    def add_node(self, node_id: str, text: str, parent_id: Optional[str] = None):
        node = DocumentGraphNode(node_id, text, parent_id)
        self.nodes[node_id] = node
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].child_ids.append(node_id)

    def get_lineage(self, node_id: str) -> List[str]:
        lineage = []
        curr = self.nodes.get(node_id)
        while curr:
            lineage.append(f"Node({curr.node_id}): {curr.text[:40]}...")
            curr = self.nodes.get(curr.parent_id) if curr.parent_id else None
        return lineage

# Verification
graph = DocumentGraphIndex()
graph.add_node("DOC_ROOT", "2025 Consolidated Financial Report")
graph.add_node("SEC_REV", "Revenue Breakdown Table", parent_id="DOC_ROOT")
graph.add_node("ROW_CLOUD", "Cloud Spend: $14.2M", parent_id="SEC_REV")

print("Data Lineage Trace:")
for step in graph.get_lineage("ROW_CLOUD"):
    print(f"  {step}")
