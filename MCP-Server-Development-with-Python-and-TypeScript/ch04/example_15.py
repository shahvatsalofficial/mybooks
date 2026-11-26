import time
from collections import defaultdict

call_history = defaultdict(list)

def rate_limit_guard(tool_name: str, max_calls: int = 5, window_sec: int = 60) -> Optional[str]:
    now = time.time()
    calls = [t for t in call_history[tool_name] if now - t < window_sec]
    call_history[tool_name] = calls
    if len(calls) >= max_calls:
        wait_sec = int(window_sec - (now - calls[0]))
        return f"RateLimitExceeded: Maximum {max_calls} calls/min reached. Retry in {wait_sec} seconds."
    call_history[tool_name].append(now)
    return None
