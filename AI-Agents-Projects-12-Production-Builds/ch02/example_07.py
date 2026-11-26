from __future__ import annotations

import difflib


def build_unified_diff(file_path: str, before: str, after: str) -> str:
    diff_lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=3,
    )
    return "".join(diff_lines)


if __name__ == "__main__":
    old = "def ping() -> str:\n    return 'pong'\n"
    new = "def ping(timeout_ms: int = 500) -> str:\n    return f'pong:{timeout_ms}'\n"
    print(build_unified_diff("service/health.py", old, new).strip())
