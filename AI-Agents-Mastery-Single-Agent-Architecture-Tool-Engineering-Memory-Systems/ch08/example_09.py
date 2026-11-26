class KubernetesHPAAdapter:
    def __init__(self, target_sessions_per_pod: int = 25):
        self.target = target_sessions_per_pod
        self.active_sessions = 0

    def register_session(self):
        self.active_sessions += 1

    def deregister_session(self):
        self.active_sessions = max(0, self.active_sessions - 1)

    def calculate_desired_replicas(self, current_replicas: int) -> int:
        total_load = self.active_sessions
        desired = math.ceil(total_load / max(1, self.target))
        return max(1, desired)

# Verification
hpa = KubernetesHPAAdapter(target_sessions_per_pod=20)
for _ in range(85):
    hpa.register_session()
print("Current Active Sessions:", hpa.active_sessions)
print("Kubernetes HPA Desired Replicas Calculated:", hpa.calculate_desired_replicas(current_replicas=2))
