from __future__ import annotations

import asyncio
import sys
import tempfile
import time
from pathlib import Path


async def run_isolated_pytest(
    work_dir: Path,
    timeout_sec: float = 10.0,
) -> SandboxVerdict:
    t0 = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(work_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        output = stdout_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode or 0
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return SandboxVerdict(
            run_id="sbx_timeout",
            exit_code=124,
            tests_passed=0,
            tests_failed=1,
            coverage_pct=0.0,
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            failure_excerpt=f"Execution exceeded {timeout_sec}s timeout and was killed.",
        )

    duration = round((time.perf_counter() - t0) * 1000, 2)
    passed = 1 if exit_code == 0 else 0
    failed = 0 if exit_code == 0 else 1
    return SandboxVerdict(
        run_id="sbx_local",
        exit_code=exit_code,
        tests_passed=passed,
        tests_failed=failed,
        coverage_pct=100.0 if exit_code == 0 else 0.0,
        duration_ms=duration,
        failure_excerpt="" if exit_code == 0 else output[-400:],
    )


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "test_sample.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertEqual(2 + 2, 4)\n",
            encoding="utf-8",
        )
        verdict = await run_isolated_pytest(root, timeout_sec=5.0)
        print(f"Verdict: green={verdict.is_green} exit={verdict.exit_code} duration={verdict.duration_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
