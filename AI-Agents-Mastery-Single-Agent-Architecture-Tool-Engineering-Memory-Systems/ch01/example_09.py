@dataclass
class ThreadNode:
    node_id: str
    parent_id: Optional[str]
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)

class BranchingThreadManager:
    def __init__(self, root_system_prompt: str):
        self.nodes: Dict[str, ThreadNode] = {}
        root = ThreadNode(node_id="root", parent_id=None, role="system", content=root_system_prompt)
        self.nodes["root"] = root
        self.active_leaf_id = "root"

    def append_message(self, role: str, content: str) -> str:
        new_id = f"node_{len(self.nodes)}_{int(time.time()*1000)%10000}"
        node = ThreadNode(node_id=new_id, parent_id=self.active_leaf_id, role=role, content=content)
        self.nodes[new_id] = node
        self.active_leaf_id = new_id
        return new_id

    def create_branch(self, from_node_id: str) -> str:
        if from_node_id not in self.nodes:
            raise KeyError(f"Node '{from_node_id}' does not exist.")
        self.active_leaf_id = from_node_id
        return self.active_leaf_id

    def get_active_trajectory(self) -> List[Dict[str, str]]:
        trajectory = []
        curr_id = self.active_leaf_id
        while curr_id:
            node = self.nodes[curr_id]
            trajectory.append({"role": node.role, "content": node.content})
            curr_id = node.parent_id
        return list(reversed(trajectory))

# Verification
thread_mgr = BranchingThreadManager("You are a financial planning agent.")
n1 = thread_mgr.append_message("user", "Scenario A: Calculate mortgage on $500k at 6%.")
n2 = thread_mgr.append_message("assistant", "Monthly payment is $2,997.75.")

# Fork to Scenario B
thread_mgr.create_branch(n1)
thread_mgr.append_message("user", "Scenario B: Calculate mortgage on $500k at 5%.")
thread_mgr.append_message("assistant", "Monthly payment is $2,684.11.")

print("Branch B Trajectory Length:", len(thread_mgr.get_active_trajectory()))
