import sys

def enforce_cicd_quality_gate(benchmark_report: Dict[str, Any], min_success_rate: float = 0.95, max_avg_steps: float = 3.5):
    tsr = benchmark_report["task_success_rate"]
    asc = benchmark_report["average_steps_to_convergence"]
    
    print("=== AGENT QUALITY GATE VERIFICATION ===")
    print(f"Task Success Rate: {tsr * 100:.2f}% (Threshold: >={min_success_rate * 100:.2f}%)")
    print(f"Avg Steps to Convergence: {asc:.2f} (Threshold: <={max_avg_steps:.2f})")
    
    failures = []
    if tsr < min_success_rate:
        failures.append(f"Task Success Rate {tsr:.4f} is below minimum threshold of {min_success_rate}")
    if asc > max_avg_steps:
        failures.append(f"Average Steps {asc:.2f} exceeded maximum allowable budget of {max_avg_steps}")
        
    if failures:
        print("\n❌ CI/CD QUALITY GATE REJECTED:")
        for f in failures:
            print(f"  - {f}")
        return False
    
    print("\n✅ CI/CD QUALITY GATE PASSED: Zero regressions detected.")
    return True

# Verification
gate_passed = enforce_cicd_quality_gate(benchmark_report, min_success_rate=0.95, max_avg_steps=3.0)
print(f"Gate Approval Status: {gate_passed}")
