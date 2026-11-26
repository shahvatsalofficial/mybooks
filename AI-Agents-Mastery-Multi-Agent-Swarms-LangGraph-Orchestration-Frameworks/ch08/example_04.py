if __name__ == "__main__":
    supervisor = ObservedSwarmSupervisor()
    result = supervisor.execute_monitored_workflow("Audit production Kubernetes container security.")
    
    print("\n--- WATERFALL TRACE SUMMARY ---")
    print(f"Root Trace ID: {result['root_trace_id']}")
    print(f"Workflow Status: {result['status']}")
    print(f"Findings: {result['findings']}")
    print(f"Remediation: {result['remediation']}")
