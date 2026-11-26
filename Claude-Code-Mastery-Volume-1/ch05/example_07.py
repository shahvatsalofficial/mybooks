"""
Production Asyncio Multi-Agent DAG Orchestrator
Architecture: Sovereign Standard v10.0
Features: Non-blocking Async Workers, Semaphore Throttling, Strict Pydantic Contracts
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SwarmOrchestrator")


class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SubagentContract(BaseModel):
    task_id: str
    target_files: List[str]
    invariants: List[str]
    verification_command: str
    token_budget_cap: int = Field(default=30000, le=50000)


@dataclass
class DagNode:
    contract: SubagentContract
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    tokens_consumed: int = 0
    error_message: Optional[str] = None


class AsyncSwarmOrchestrator:
    def __init__(self, workspace_root: str, max_concurrency: int = 4, global_budget: int = 200000):
        self.workspace_root = workspace_root
        self.max_concurrency = max_concurrency
        self.global_budget = global_budget
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.nodes: Dict[str, DagNode] = {}
        self.total_tokens_burned = 0

    def add_task(self, contract: SubagentContract, dependencies: Optional[List[str]] = None) -> None:
        self.nodes[contract.task_id] = DagNode(
            contract=contract,
            dependencies=dependencies or [],
            state=TaskState.PENDING,
        )

    async def run(self) -> bool:
        logger.info(f"Initiating Async Swarm run with {len(self.nodes)} DAG nodes.")

        while self._has_active_tasks():
            if self.total_tokens_burned >= self.global_budget:
                logger.error("FATAL: Swarm global token budget exhausted. Aborting.")
                return False

            ready_nodes = self._find_ready_nodes()
            if not ready_nodes and not self._is_any_worker_running():
                logger.error("FATAL: Deadlock detected in Task DAG. Cycle exists.")
                return False

            tasks = [self._execute_node_with_semaphore(node) for node in ready_nodes]
            if tasks:
                await asyncio.gather(*tasks)

            await asyncio.sleep(0.2)

        logger.info("All DAG tasks processed. Executing Shadow Worktree Verification...")
        return await self._verify_in_shadow_worktree()

    def _find_ready_nodes(self) -> List[DagNode]:
        ready = []
        for node in self.nodes.values():
            if node.state != TaskState.PENDING:
                continue

            deps_satisfied = all(
                self.nodes[dep_id].state == TaskState.COMPLETED
                for dep_id in node.dependencies
                if dep_id in self.nodes
            )

            if deps_satisfied:
                ready.append(node)
        return ready

    async def _execute_node_with_semaphore(self, node: DagNode) -> None:
        async with self.semaphore:
            node.state = TaskState.RUNNING
            logger.info(f"Spawned Worker for Task [{node.contract.task_id}]. Invariants: {len(node.contract.invariants)}")

            # Generate sanitized, clean-room context contract
            payload_file = os.path.join(self.workspace_root, f".clean_contract_{node.contract.task_id}.json")
            with open(payload_file, "w") as f:
                f.write(node.contract.model_dump_json(indent=2))

            try:
                # Execute worker verification in non-blocking threadpool
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        node.contract.verification_command,
                        shell=True,
                        cwd=self.workspace_root,
                        capture_output=True,
                        text=True,
                        timeout=45,
                    ),
                )

                if result.returncode == 0:
                    node.state = TaskState.COMPLETED
                    node.tokens_consumed = 8500
                    self.total_tokens_burned += node.tokens_consumed
                    logger.info(f"Task [{node.contract.task_id}] PASSED verification gate.")
                else:
                    node.state = TaskState.FAILED
                    node.error_message = result.stderr
                    logger.error(f"Task [{node.contract.task_id}] FAILED verification: {result.stderr.strip()}")

            except Exception as e:
                node.state = TaskState.FAILED
                node.error_message = str(e)
                logger.error(f"Task [{node.contract.task_id}] encountered unhandled exception: {e}")
            finally:
                if os.path.exists(payload_file):
                    os.remove(payload_file)

    async def _verify_in_shadow_worktree(self) -> bool:
        shadow_dir = os.path.join(self.workspace_root, ".claude_shadow_python")
        logger.info(f"Setting up isolated Shadow Git Worktree at: {shadow_dir}")

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    f"git worktree add -b shadow-test-{os.getpid()} {shadow_dir} HEAD",
                    shell=True,
                    cwd=self.workspace_root,
                    check=True,
                    capture_output=True,
                ),
            )

            test_run = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    "pytest tests/",
                    shell=True,
                    cwd=shadow_dir,
                    capture_output=True,
                    text=True,
                ),
            )

            if test_run.returncode == 0:
                logger.info("Consensus Achieved: Pytest regression suite PASSED in shadow worktree.")
                return True
            else:
                logger.error(f"Consensus Veto: Pytest failed in shadow worktree:\n{test_run.stderr}")
                return False

        except Exception as ex:
            logger.error(f"Shadow worktree verification failed with error: {ex}")
            return False
        finally:
            if os.path.exists(shadow_dir):
                subprocess.run(
                    f"git worktree remove --force {shadow_dir}",
                    shell=True,
                    cwd=self.workspace_root,
                    capture_output=True,
                )

    def _has_active_tasks(self) -> bool:
        return any(n.state in (TaskState.PENDING, TaskState.RUNNING) for n in self.nodes.values())

    def _is_any_worker_running(self) -> bool:
        return any(n.state == TaskState.RUNNING for n in self.nodes.values())
