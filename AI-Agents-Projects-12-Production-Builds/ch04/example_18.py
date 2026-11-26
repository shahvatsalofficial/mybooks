from decimal import Decimal
import re

PAREN_RE = re.compile(r"^\(\s*\$?\s*([\d,]+(?:\.\d+)?)\s*\)$")

def parse_num(raw: str) -> Decimal:
    m = PAREN_RE.match(raw.strip())
    if m:
        return -Decimal(m.group(1).replace(",", ""))
    return Decimal(raw.replace("$", "").replace(",", "").strip())

for sample in ("$3,120.50", "(1,420.00)", "0"):
    print(sample, "->", parse_num(sample))
