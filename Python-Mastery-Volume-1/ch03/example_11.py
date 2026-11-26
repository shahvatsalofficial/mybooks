from collections import Counter

# Leverages C-accelerated _count_elements loop
token_counts = Counter(word_stream)

# Top 10 elements computed in O(N log K) time via heapq.nlargest
top_tokens = token_counts.most_common(10)
