class EphemeralCrewPool:
    def __init__(self):
        self.active_workers: List[Agent] = []

    def spawn_worker(self, domain_skill: str) -> Agent:
        worker_id = f"Worker_{domain_skill}_{uuid.uuid4().hex[:4]}"
        print(f"[CREW POOL] Dynamically provisioning ephemeral agent '{worker_id}'...")
        agent = Agent(
            role=f"Ephemeral {domain_skill} Specialist",
            goal=f"Execute rapid {domain_skill} subtasks",
            backstory="High-speed stateless cloud worker",
            verbose=False,
            allow_delegation=False
        )
        self.active_workers.append(agent)
        return agent
