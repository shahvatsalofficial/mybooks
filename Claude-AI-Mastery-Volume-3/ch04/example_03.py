"""
Recipe 04.3: Distributed Agent Deadlock Detector & Preemptive Lock Manager.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import time
import logging
from typing import Dict, List, Set, Optional
from pydantic import BaseModel

logger = logging.getLogger("DeadlockDetector")
logger.setLevel(logging.INFO)


class ResourceLock(BaseModel):
    resource_id: str
    held_by_agent: str
    acquired_at: float
    priority_level: int # Higher number = higher operational priority


class DistributedDeadlockGovernor:
    """
    Maintains the global Wait-For Graph (WFG) for autonomous agents.
    Detects directed cycles using Tarjan's SCC algorithm and preempts the lowest-priority node.
    """

    def __init__(self):
        # resource_id -> ResourceLock
        self.active_locks: Dict[str, ResourceLock] = {}
        # waiting_agent_id -> target_resource_id
        self.wait_for_map: Dict[str, str] = {}
        # agent_id -> priority
        self.agent_priorities: Dict[str, int] = {}

    def acquire_lock(self, agent_id: str, resource_id: str, priority: int = 10) -> bool:
        """
        Attempts to acquire an exclusive lock. If held, registers wait edge and scans for deadlocks.
        """
        self.agent_priorities[agent_id] = priority

        if resource_id not in self.active_locks:
            # Lock is free; grant immediately
            self.active_locks[resource_id] = ResourceLock(
                resource_id=resource_id,
                held_by_agent=agent_id,
                acquired_at=time.time(),
                priority_level=priority
            )
            if agent_id in self.wait_for_map:
                del self.wait_for_map[agent_id]
            logger.info(f"Agent [{agent_id}] acquired lock on [{resource_id}]")
            return True

        # Lock is currently held by another agent; register dependency edge
        holder = self.active_locks[resource_id].held_by_agent
        if holder == agent_id:
            return True # Reentrant acquisition

        self.wait_for_map[agent_id] = resource_id
        logger.warning(f"Agent [{agent_id}] blocked waiting for [{resource_id}] held by [{holder}]")

        # Scan for deadlocks
        cycle = self._detect_deadlock_cycle()
        if cycle:
            logger.error(f"DEADLOCK DETECTED! Circular cycle: {' -> '.join(cycle)}")
            self._resolve_deadlock(cycle)
            return False

        return False

    def release_lock(self, agent_id: str, resource_id: str) -> None:
        """Releases lock and removes waiting references."""
        if resource_id in self.active_locks:
            if self.active_locks[resource_id].held_by_agent == agent_id:
                del self.active_locks[resource_id]
                logger.info(f"Agent [{agent_id}] released lock on [{resource_id}]")

        if agent_id in self.wait_for_map:
            del self.wait_for_map[agent_id]

    def _detect_deadlock_cycle(self) -> Optional[List[str]]:
        """
        Constructs adjacency graph from wait_for_map and runs DFS cycle detection.
        """
        # Build adjacency graph: agent_A -> agent_B (A waits for B)
        adj: Dict[str, str] = {}
        for waiter, res_id in self.wait_for_map.items():
            if res_id in self.active_locks:
                holder = self.active_locks[res_id].held_by_agent
                adj[waiter] = holder

        # Detect cycle via cycle chasing
        for start_node in adj:
            visited = []
            curr = start_node
            while curr in adj:
                visited.append(curr)
                curr = adj[curr]
                if curr in visited:
                    cycle_start_idx = visited.index(curr)
                    return visited[cycle_start_idx:] + [curr]
        return None

    def _resolve_deadlock(self, cycle: List[str]) -> None:
        """
        Selects lowest priority agent in cycle and revokes its lock to break the deadlock.
        """
        unique_agents = list(dict.fromkeys(cycle))
        # Find agent with minimum priority level
        preempt_target = min(unique_agents, key=lambda a: self.agent_priorities.get(a, 0))
        logger.warning(f"Preempting lowest priority agent [{preempt_target}] to break deadlock cycle.")

        # Find locks held by preempt_target and revoke them
        revoked_resources = [r_id for r_id, lock in self.active_locks.items() if lock.held_by_agent == preempt_target]
        for r_id in revoked_resources:
            del self.active_locks[r_id]
            logger.info(f"Revoked lock [{r_id}] from preempted agent [{preempt_target}]")

        if preempt_target in self.wait_for_map:
            del self.wait_for_map[preempt_target]
