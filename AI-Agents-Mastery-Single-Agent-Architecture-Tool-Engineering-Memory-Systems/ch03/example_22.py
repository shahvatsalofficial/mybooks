import subprocess
import re

def secure_fetch_service_logs(service_name: str) -> str:
    # 1. Enforce strict RFC 1123 DNS label regex
    if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", service_name):
        raise ValueError(f"Security Alert: Illegal service name format '{service_name}'.")
    
    # 2. Never use shell=True; pass explicit argument arrays
    cmd = ["kubectl", "logs", "-l", f"app={service_name}", "--tail=100"]
    return subprocess.check_output(cmd, shell=False, timeout=5.0).decode("utf-8")
