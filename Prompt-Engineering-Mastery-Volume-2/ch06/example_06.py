import sys
import json
from typing import List, Dict, Any
from pydantic import BaseModel
from anthropic import Anthropic

class BenchmarkCase(BaseModel):
    id: str
    jurisdiction: str
    raw_invoice_input: str
    expected_vat_rate: float
    expected_vat_amount: float

def run_ci_cd_prompt_gate(candidate_prompt_path: str, golden_dataset_path: str):
    with open(candidate_prompt_path, "r") as f:
        candidate_prompt = f.read()

    with open(golden_dataset_path, "r") as f:
        cases = [BenchmarkCase(**item) for item in json.load(f)]

    client = Anthropic()
    regressions = []
    
    print(f"🔬 Running automated evaluation across {len(cases)} golden test cases...")

    for case in cases:
        res = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            temperature=0.0,
            system=candidate_prompt,
            messages=[{"role": "user", "content": case.raw_invoice_input}]
        )
        
        # Parse extracted VAT amount
        try:
            parsed = json.loads(res.content[0].text)
            actual_vat = float(parsed.get("vat_amount", -1))
            delta = abs(actual_vat - case.expected_vat_amount)
            if delta > 0.01:
                regressions.append({
                    "case_id": case.id,
                    "jurisdiction": case.jurisdiction,
                    "expected": case.expected_vat_amount,
                    "actual": actual_vat,
                    "delta": delta
                })
        except Exception as e:
            regressions.append({"case_id": case.id, "error": str(e)})

    # Strict Zero-Regression Tolerance Policy
    if regressions:
        print(f"❌ CI/CD REJECTION: Detected {len(regressions)} financial regression failures!")
        for r in regressions[:5]:
            print(f"   -> Failed Case {r['case_id']} ({r.get('jurisdiction')}): Expected {r.get('expected')} but got {r.get('actual')}")
        sys.exit(1)

    print("✅ CI/CD SUCCESS: Zero regressions detected across 100% of benchmark test cases.")
    sys.exit(0)
