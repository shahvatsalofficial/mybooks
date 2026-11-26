def boost_priority(base_score: int, duplicate_channel_count: int) -> int:
    return min(1000, base_score + (duplicate_channel_count * 75))

print("Base 750 + 2 duplicate pings:", boost_priority(750, 2))
