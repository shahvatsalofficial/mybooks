from __future__ import annotations

import re


def has_implicit_or_cross_join(sql: str) -> bool:
    if re.search(r"\bCROSS\s+JOIN\b", sql, re.IGNORECASE):
        return True
    from_match = re.search(
        r"\bFROM\b([\s\S]*?)(?:\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|$)",
        sql,
        re.IGNORECASE,
    )
    if from_match and "," in from_match.group(1):
        return True
    return False


if __name__ == "__main__":
    print("Implicit comma join:", has_implicit_or_cross_join("SELECT a.id FROM a, b WHERE a.id = b.id"))
    print("Explicit INNER JOIN:", has_implicit_or_cross_join("SELECT a.id FROM a JOIN b ON a.id = b.id"))
