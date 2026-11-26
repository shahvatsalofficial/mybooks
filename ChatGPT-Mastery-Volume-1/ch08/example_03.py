"""
Architectural Drill 1: High-Precision Contract Clause Tokenizer
"""

import re
from typing import List, Dict, Any

CLAUSE_REGEX = re.compile(
    r'(?:^|\n)(?:Section\s+|Article\s+)?(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n\.\:]{2,80})[\.\:\n]+(.*?)(?=(?:\n(?:Section\s+|Article\s+)?\d+(?:\.\d+)*\.?\s+[A-Z])|\Z)',
    re.DOTALL | re.MULTILINE
)

def tokenize_contract_clauses(contract_text: str) -> List[Dict[str, Any]]:
    clauses = []
    for match in CLAUSE_REGEX.finditer(contract_text):
        identifier = match.group(1).strip()
        title = match.group(2).strip()
        body = match.group(3).strip()
        
        # Word count calculation for validation
        word_count = len(body.split())
        
        clauses.append({
            "identifier": identifier,
            "title": title,
            "body": body,
            "word_count": word_count
        })
    return clauses

# Verification Test
sample_contract = """
Section 1.1 Definitions. Capitalized terms in this Agreement have specified meanings.
Section 1.2 Term and Termination. This Agreement shall commence on the Effective Date.
Section 1.3 Limitation of Liability. Neither party shall be liable for indirect damages.
"""
parsed = tokenize_contract_clauses(sample_contract)
assert len(parsed) == 3
assert parsed[2]["identifier"] == "1.3"
assert parsed[2]["title"] == "Limitation of Liability"
