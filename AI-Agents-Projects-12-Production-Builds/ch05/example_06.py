from __future__ import annotations

import asyncio
from enum import Enum
from pydantic import BaseModel, Field


class DiagState(str, Enum):
    INSPECT_PODS = "inspect_pods"
    INSPECT_EVENTS = "inspect_events"
    FETCH_PREV_LOGS = "fetch_prev_logs"
    INSPECT_REPLICASETS = "inspect_replicasets"
    COMPLETE = "complete"


class PodSnapshot(BaseModel):
    pod_name: str
    phase: str
    restart_count: int
    last_exit_code: int | None = None
    termination_reason: str | None = None


class DiagnosticReport(BaseModel):
    namespace: str
    service: str
    steps_executed: int
    unhealthy_pods: list[PodSnapshot]
    warning_events: list[str]
    recommended_runbook_id: str
    confidence: float = Field(ge=0.0, le=1.0)


class ReadOnlyK8sDiagGraph:
    def __init__(self, namespace: str, service: str, max_steps: int = 8) -> None:
        self.namespace = namespace
        self.service = service
        self.max_steps = max_steps
        self.state = DiagState.INSPECT_PODS
        self.steps = 0
        self.pods: list[PodSnapshot] = []
        self.events: list[str] = []
        self.prev_log_excerpt: str = ""
        self.active_rs_revision: int = 0

    async def run(self) -> DiagnosticReport:
        while self.state != DiagState.COMPLETE and self.steps < self.max_steps:
            self.steps += 1
            if self.state == DiagState.INSPECT_PODS:
                await self._step_inspect_pods()
                self.state = DiagState.INSPECT_EVENTS
            elif self.state == DiagState.INSPECT_EVENTS:
                await self._step_inspect_events()
                self.state = DiagState.FETCH_PREV_LOGS
            elif self.state == DiagState.FETCH_PREV_LOGS:
                await self._step_fetch_prev_logs()
                self.state = DiagState.INSPECT_REPLICASETS
            elif self.state == DiagState.INSPECT_REPLICASETS:
                await self._step_inspect_replicasets()
                self.state = DiagState.COMPLETE

        unhealthy = [p for p in self.pods if p.restart_count > 0 or p.phase != "Running"]
        runbook = "RB-ROLLBACK-DEPLOYMENT" if self.active_rs_revision > 1 else "RB-RESTART-DEPLOYMENT"
        return DiagnosticReport(
            namespace=self.namespace,
            service=self.service,
            steps_executed=self.steps,
            unhealthy_pods=unhealthy,
            warning_events=self.events,
            recommended_runbook_id=runbook,
            confidence=0.94 if unhealthy else 0.50,
        )

    async def _step_inspect_pods(self) -> None:
        await asyncio.sleep(0.01)
        self.pods = [
            PodSnapshot(
                pod_name="checkout-orchestrator-7d9b-x4k2p",
                phase="CrashLoopBackOff",
                restart_count=6,
                last_exit_code=137,
                termination_reason="Error",
            ),
            PodSnapshot(
                pod_name="checkout-orchestrator-7d9b-m9q1z",
                phase="CrashLoopBackOff",
                restart_count=5,
                last_exit_code=1,
                termination_reason="Error",
            ),
        ]

    async def _step_inspect_events(self) -> None:
        await asyncio.sleep(0.01)
        self.events = [
            "Warning BackOff: Back-off restarting failed container checkout-orchestrator",
            "Warning Unhealthy: Readiness probe failed: HTTP probe failed with statuscode: 503",
        ]

    async def _step_fetch_prev_logs(self) -> None:
        await asyncio.sleep(0.01)
        self.prev_log_excerpt = "FATAL: sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached"

    async def _step_inspect_replicasets(self) -> None:
        await asyncio.sleep(0.01)
        self.active_rs_revision = 42


async def main() -> None:
    graph = ReadOnlyK8sDiagGraph(namespace="prod-payments", service="checkout-orchestrator")
    report = await graph.run()
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
