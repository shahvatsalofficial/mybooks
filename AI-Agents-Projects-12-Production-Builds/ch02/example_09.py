from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxConfig:
    image: str = "python:3.12-slim"
    memory_limit: str = "512m"
    cpus: str = "1.0"
    pids_limit: int = 64
    timeout_sec: int = 30


def build_docker_pytest_command(
    workspace_dir: Path,
    test_target: str,
    cfg: SandboxConfig,
) -> list[str]:
    mount_spec = f"{workspace_dir.resolve()}:/workspace:rw"
    return [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        f"--memory={cfg.memory_limit}",
        f"--cpus={cfg.cpus}",
        f"--pids-limit={cfg.pids_limit}",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",
        "-v",
        mount_spec,
        "-w",
        "/workspace",
        cfg.image,
        "pytest",
        "-q",
        "--tb=short",
        test_target,
    ]


if __name__ == "__main__":
    cmd = build_docker_pytest_command(Path("/tmp/repo_clone"), "tests/test_fees.py", SandboxConfig())
    print("Sandbox CLI:", " ".join(cmd))
