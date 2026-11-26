import json
import sys
from pathlib import Path

def evaluate_review(report_path: str) -> int:
    raw = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if raw.get("is_error"):
        print(f"ERROR: Claude execution failed: {raw.get('result')}", file=sys.stderr)
        return 2

    structured = raw.get("structured_output") or json.loads(raw["result"])
    findings = structured.get("findings", [])
    for idx, item in enumerate(findings, start=1):
        print(f"[{idx}] {item}")

    if structured.get("blocking") is True:
        print("GATE FAILED: Blocking issues detected.", file=sys.stderr)
        return 1

    print(f"GATE PASSED: {len(findings)} advisory notes, 0 blockers.")
    return 0

if __name__ == "__main__":
    raise SystemExit(evaluate_review(sys.argv[1]))
