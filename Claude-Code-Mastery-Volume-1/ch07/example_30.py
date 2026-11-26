# Execution verification snippet
auditor = CanaryHealthAuditor(
    prometheus_url="http://localhost:9090",
    service_name="auth-service",
    max_p99_latency_ms=120.0,
    max_error_rate_pct=0.5
)

snapshot = auditor.capture_metrics(is_canary=True)
audit = auditor.evaluate_statistical_anomaly(snapshot)

if audit["breached"]:
    print(f"ANOMALY CONFIRMED: {audit['reasons']}")
    auditor.execute_emergency_rollback()
    # Generates autopsy report in under 5 seconds
