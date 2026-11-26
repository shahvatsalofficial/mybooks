"""
Recipe 08.6: Real-Time Token Velocity Anomaly Detector
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import time
import collections
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("AnomalyDetector")

class RunawayAgentBreaker:
    def __init__(self, max_tokens_per_minute: int = 150000, max_identical_tool_calls: int = 4):
        self.max_tpm = max_tokens_per_minute
        self.max_identical_calls = max_identical_tool_calls
        # Sliding window of token consumption: (timestamp, tokens)
        self.token_history: collections.deque = collections.deque()
        # History of recent tool calls: tool_name
        self.tool_call_history: collections.deque = collections.deque(maxlen=10)

    def record_and_verify(self, tool_name: Optional[str], tokens_consumed: int) -> bool:
        """Verifies whether the current execution breaches velocity or repetitive loop ceilings."""
        now = time.time()
        self.token_history.append((now, tokens_consumed))
        if tool_name:
            self.tool_call_history.append(tool_name)

        # 1. Prune events older than 60 seconds
        while self.token_history and self.token_history[0][0] < now - 60.0:
            self.token_history.popleft()

        # 2. Check 60-second rolling token velocity
        rolling_tokens = sum(t[1] for t in self.token_history)
        if rolling_tokens > self.max_tpm:
            logger.critical(
                f"[EMERGENCY BREAKER] Rolling token velocity breached ceiling: "
                f"{rolling_tokens:,} tokens in last 60s (Limit: {self.max_tpm:,}). TRIPPING BREAKER!"
            )
            return False

        # 3. Detect redundant identical tool loop (e.g. repeated failed SQL query)
        if tool_name and len(self.tool_call_history) >= self.max_identical_calls:
            recent_slice = list(self.tool_call_history)[-self.max_identical_calls:]
            if all(call == tool_name for call in recent_slice):
                logger.critical(
                    f"[EMERGENCY BREAKER] Detected infinite agent loop! Tool '{tool_name}' "
                    f"invoked {self.max_identical_calls} consecutive times without progress. HALTING RUNTIME!"
                )
                return False

        return True
