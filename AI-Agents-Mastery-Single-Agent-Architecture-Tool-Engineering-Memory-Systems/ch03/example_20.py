def fetch_service_logs(service_name: str) -> str:
    # VULNERABLE: Direct string interpolation into bash
    cmd = f"kubectl logs -l app={service_name} --tail=100"
    return subprocess.check_output(cmd, shell=True).decode()
