"""
Recipe 05.2: Programmatic py-spy Native Stack Sampler & Flamegraph Export
Architecture: In-process trigger spawning out-of-band py-spy flamegraph recording.
Target Runtime: Python 3.12+ (Linux/macOS)
"""

from __future__ import annotations
import os
import shutil
import subprocess
import time
from typing import Optional


class PySpyAutoProfiler:
    """Spawns an out-of-band py-spy profiler when triggered by production alerts."""

    def __init__(self, output_dir: str = "/tmp/profiles") -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._pyspy_bin = shutil.which("py-spy")
        if not self._pyspy_bin:
            # Fallback path if installed in virtual environment
            import sys
            candidate = os.path.join(os.path.dirname(sys.executable), "py-spy")
            if os.path.exists(candidate):
                self._pyspy_bin = candidate

    def capture_flamegraph(
        self,
        duration_seconds: int = 10,
        sampling_rate_hz: int = 100,
        include_native_c: bool = True,
    ) -> Optional[str]:
        """Captures an SVG flamegraph of the current process without interrupting execution.
        
        Args:
            duration_seconds: Duration to sample the target process.
            sampling_rate_hz: Sampling frequency in Hertz (samples/second).
            include_native_c: If True, includes native C/Rust stack frames.
            
        Returns:
            Path to the generated SVG flamegraph file, or None if py-spy is unavailable.
        """
        if not self._pyspy_bin:
            print("py-spy executable not found in PATH or venv. Install via: pip install py-spy")
            return None

        current_pid = os.getpid()
        timestamp = int(time.time())
        output_svg = os.path.join(self.output_dir, f"profile_pid{current_pid}_{timestamp}.svg")

        cmd = [
            self._pyspy_bin,
            "record",
            "-o", output_svg,
            "-p", str(current_pid),
            "-d", str(duration_seconds),
            "-r", str(sampling_rate_hz),
            "--format", "flamegraph",
        ]

        if include_native_c:
            cmd.append("--native")  # Interrogate C/C++ native call stacks via DWARF symbols

        print(f"Launching out-of-band py-spy capture (PID: {current_pid}) for {duration_seconds}s...")
        # Launch non-blocking background subprocess
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()

        if proc.returncode == 0 and os.path.exists(output_svg):
            print(f"Flamegraph successfully generated: {output_svg}")
            return output_svg
        else:
            _, err = proc.communicate()
            print(f"py-spy execution failed (code {proc.returncode}): {err.decode('utf-8', errors='ignore')}")
            return None


if __name__ == "__main__":
    profiler = PySpyAutoProfiler()
    print(f"Profiler initialized with binary: {profiler._pyspy_bin}")
