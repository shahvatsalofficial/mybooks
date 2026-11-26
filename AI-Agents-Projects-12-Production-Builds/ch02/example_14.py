from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorktreePlan:
    job_id: str
    worktree_path: Path
    branch_name: str
    create_cmd: list[str]
    cleanup_cmd: list[str]


def plan_git_worktree(repo_root: Path, job_id: str, base_ref: str = "main") -> WorktreePlan:
    wt_path = repo_root.parent / f"wt_{job_id}"
    branch = f"agent/refactor-{job_id}"
    return WorktreePlan(
        job_id=job_id,
        worktree_path=wt_path,
        branch_name=branch,
        create_cmd=["git", "-C", str(repo_root), "worktree", "add", "-b", branch, str(wt_path), base_ref],
        cleanup_cmd=["git", "-C", str(repo_root), "worktree", "remove", "--force", str(wt_path)],
    )


if __name__ == "__main__":
    plan = plan_git_worktree(Path("/repos/settlement-core"), "job_4401")
    print("Create :", " ".join(plan.create_cmd))
    print("Cleanup:", " ".join(plan.cleanup_cmd))
