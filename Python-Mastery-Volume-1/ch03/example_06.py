import bisect

# Pre-sorted financial latency SLA threshold buckets (microseconds)
SLA_BUCKETS = [50, 100, 250, 500, 1000, 5000, 10000]
SLA_LABELS  = ["p50", "p75", "p90", "p95", "p99", "p99.9", "breach"]

def categorize_latency(latency_us: int) -> str:
    # bisect_right executes binary search in C in ~45 nanoseconds!
    index = bisect.bisect_right(SLA_BUCKETS, latency_us)
    return SLA_LABELS[min(index, len(SLA_LABELS) - 1)]
