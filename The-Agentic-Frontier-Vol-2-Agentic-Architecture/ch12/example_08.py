# rollback_controller.py
"""
Automated Rollback Controller for Agentic CI/CD pipelines.
Monitors evaluation score windows and executes rollback when thresholds are breached.
"""
import time
import logging
from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional
import threading

logger = logging.getLogger("rollback-controller")


@dataclass
class RollbackConfig:
    overall_score_threshold: float = 0.82
    safety_score_threshold: float = 0.95
    min_sample_window: int = 100
    window_minutes: int = 15
    tolerance_pct: float = 0.03  # 3% degradation tolerance before triggering


class RollbackController:
    def __init__(
        self,
        config: RollbackConfig,
        rollback_fn: Callable,
        notify_fn: Callable,
        current_version: str,
        stable_version: str
    ):
        self.config = config
        self.rollback_fn = rollback_fn
        self.notify_fn = notify_fn
        self.current_version = current_version
        self.stable_version = stable_version
        self.eval_window: deque = deque(maxlen=1000)
        self.rollback_triggered = False
        self._lock = threading.Lock()

    def ingest_eval_result(self, overall: float, safety: float, timestamp: float):
        with self._lock:
            self.eval_window.append({
                "overall": overall,
                "safety": safety,
                "timestamp": timestamp
            })
            self._check_thresholds()

    def _check_thresholds(self):
        if self.rollback_triggered:
            return

        cutoff = time.time() - (self.config.window_minutes * 60)
        recent = [r for r in self.eval_window if r["timestamp"] >= cutoff]

        if len(recent) < self.config.min_sample_window:
            return  # Not enough data yet

        avg_overall = sum(r["overall"] for r in recent) / len(recent)
        avg_safety = sum(r["safety"] for r in recent) / len(recent)

        overall_breached = avg_overall < (
            self.config.overall_score_threshold * (1 - self.config.tolerance_pct)
        )
        safety_breached = avg_safety < self.config.safety_score_threshold

        if overall_breached or safety_breached:
            logger.critical(
                f"ROLLBACK TRIGGERED: overall={avg_overall:.3f} "
                f"(threshold={self.config.overall_score_threshold}), "
                f"safety={avg_safety:.3f} "
                f"(threshold={self.config.safety_score_threshold})"
            )
            self.rollback_triggered = True
            self.rollback_fn(
                from_version=self.current_version,
                to_version=self.stable_version,
                reason="eval_degradation",
                metrics={
                    "avg_overall": avg_overall,
                    "avg_safety": avg_safety,
                    "sample_count": len(recent)
                }
            )
            self.notify_fn(
                title=f"AGENT ROLLBACK: {self.current_version} → {self.stable_version}",
                body=f"Eval degradation detected. Overall: {avg_overall:.3f}. "
                     f"Safety: {avg_safety:.3f}. Auto-rollback completed."
            )
