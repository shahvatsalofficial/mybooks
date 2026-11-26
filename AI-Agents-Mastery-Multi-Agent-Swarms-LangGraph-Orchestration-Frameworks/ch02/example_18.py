class CheckpointNamespaceManager:
    @staticmethod
    def derive_subgraph_thread_id(parent_thread_id: str, subgraph_name: str, step_number: int) -> str:
        """Generates deterministic, isolated checkpoint keys for nested subgraphs."""
        return f"{parent_thread_id}::subgraph::{subgraph_name}::step_{step_number:04d}"

    @staticmethod
    def parse_namespace(composite_thread_id: str) -> Dict[str, str]:
        parts = composite_thread_id.split("::")
        return {
            "root_thread_id": parts[0],
            "subgraph_name": parts[2] if len(parts) > 2 else "root",
            "step": parts[3] if len(parts) > 3 else "0"
        }
