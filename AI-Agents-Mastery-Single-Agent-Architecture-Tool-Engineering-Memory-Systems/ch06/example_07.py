@dataclass
class HierarchicalNode:
    node_id: str
    text: str
    is_summary: bool
    children: List['HierarchicalNode'] = field(default_factory=list)

class HierarchicalTreeIndex:
    def __init__(self):
        self.root_nodes: List[HierarchicalNode] = []

    def add_section(self, section_title: str, summary: str, paragraphs: List[str]):
        parent = HierarchicalNode(node_id=f"summary_{section_title}", text=summary, is_summary=True)
        for idx, p in enumerate(paragraphs):
            child = HierarchicalNode(node_id=f"leaf_{section_title}_{idx}", text=p, is_summary=False)
            parent.children.append(child)
        self.root_nodes.append(parent)

    def route_query(self, query: str) -> List[str]:
        # Step 1: Match against high-level summaries
        relevant_leaves = []
        for parent in self.root_nodes:
            if any(term in parent.text.lower() for term in query.lower().split()):
                # Step 2: Traverse into children
                relevant_leaves.extend([c.text for c in parent.children])
        return relevant_leaves

# Verification
tree = HierarchicalTreeIndex()
tree.add_section(
    section_title="Security_Protocol",
    summary="Enterprise authentication, mTLS, and zero trust architecture guidelines.",
    paragraphs=["All external API clients must present an X.509 certificate.", "Tokens expire after 15 minutes."]
)
print("Tree Traversal Retrieved Leaves:", len(tree.route_query("mTLS authentication")))
