# CATASTROPHIC FLAW IN PRODUCTION FEATURE EXTRACTOR:
def extract_feature_metric(record: dict, key: str) -> float:
    # Key 'bid_floor' could be an int (10), a float (10.5), a string ('10.5'), or None!
    raw = record.get(key, 0)
    # The addition opcode below is executed 500,000 times/second:
    return raw + 1.0  # FLAW: raw alternates continuously between int and float!
