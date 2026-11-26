class SwarmTopologyController:
    def __init__(self):
        self.active_topology = "SUPERVISOR_WORKER"

    def reconfigure_topology(self, remaining_budget_usd: float, active_incident_p0: bool):
        if active_incident_p0:
            print("[TOPOLOGY CONTROLLER] P0 Incident detected! Shifting to HIERARCHICAL_TREE for deep audit.")
            self.active_topology = "HIERARCHICAL_TREE"
        elif remaining_budget_usd < 0.10:
            print(f"[TOPOLOGY CONTROLLER] Low budget (${remaining_budget_usd:.2f})! Shifting to SEQUENTIAL_PIPELINE.")
            self.active_topology = "SEQUENTIAL_PIPELINE"
        else:
            self.active_topology = "SUPERVISOR_WORKER"
        return self.active_topology
