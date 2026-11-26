"""
Architectural Drill 3: Legal Typographical Redline Generator
"""

import difflib

def generate_legal_redline(original_text: str, amended_text: str) -> str:
    orig_words = original_text.split()
    amend_words = amended_text.split()
    
    matcher = difflib.SequenceMatcher(None, orig_words, amend_words)
    redline_tokens = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            redline_tokens.extend(orig_words[i1:i2])
        elif tag == 'delete':
            deleted = " ".join(orig_words[i1:i2])
            redline_tokens.append(f"~~{deleted}~~")
        elif tag == 'insert':
            inserted = " ".join(amend_words[j1:j2])
            redline_tokens.append(f"**<u>{inserted}</u>**")
        elif tag == 'replace':
            deleted = " ".join(orig_words[i1:i2])
            inserted = " ".join(amend_words[j1:j2])
            redline_tokens.append(f"~~{deleted}~~ **<u>{inserted}</u>**")
            
    return " ".join(redline_tokens)

# Verification Test
orig = "Vendor liability is capped at 1 month of fees."
amend = "Vendor liability is capped at 12 months of total fees."
diff = generate_legal_redline(orig, amend)
assert "~~1 month of~~" in diff
assert "**<u>12 months of total</u>**" in diff
