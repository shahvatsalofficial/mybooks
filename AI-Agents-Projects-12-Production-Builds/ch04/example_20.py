import re

def validate_percentages(memo: str, approved_pcts: set[str]) -> list[str]:
    found = set(re.findall(r"-?\d+(?:\.\d+)?%", memo))
    return sorted(found - approved_pcts)

print("Unapproved:", validate_percentages("FCF margin was 13.24% (up from 18.40%).", {"13.24%"}))
