"""
Architectural Drill 5: Omnichannel Asset Conformance Validator
"""

from typing import Dict, List, Tuple

PLATFORM_CONSTRAINTS = {
    "twitter_tweet": {"min_chars": 20, "max_chars": 280},
    "linkedin_post": {"min_chars": 800, "max_chars": 2500},
    "email_subject": {"min_chars": 15, "max_chars": 65},
    "executive_summary": {"min_words": 150, "max_words": 350}
}

def validate_omnichannel_assets(assets: Dict[str, str]) -> Dict[str, Tuple[bool, str]]:
    results = {}
    for platform, content in assets.items():
        if platform not in PLATFORM_CONSTRAINTS:
            results[platform] = (False, f"Unrecognized platform: {platform}")
            continue
            
        rules = PLATFORM_CONSTRAINTS[platform]
        char_len = len(content)
        word_count = len(content.split())
        
        if "max_chars" in rules and char_len > rules["max_chars"]:
            results[platform] = (False, f"Character length {char_len} exceeds max {rules['max_chars']}.")
        elif "min_chars" in rules and char_len < rules["min_chars"]:
            results[platform] = (False, f"Character length {char_len} below min {rules['min_chars']}.")
        elif "max_words" in rules and word_count > rules["max_words"]:
            results[platform] = (False, f"Word count {word_count} exceeds max {rules['max_words']}.")
        elif "min_words" in rules and word_count < rules["min_words"]:
            results[platform] = (False, f"Word count {word_count} below min {rules['min_words']}.")
        else:
            results[platform] = (True, "Compliant")
            
    return results

# Verification Test
sample_assets = {
    "twitter_tweet": "Excited to launch our new enterprise DuPont financial analysis engine! #FinTech #AI",
    "email_subject": "Q3 Enterprise Financial Automation Report"
}
validation = validate_omnichannel_assets(sample_assets)
assert validation["twitter_tweet"][0] == True
assert validation["email_subject"][0] == True
