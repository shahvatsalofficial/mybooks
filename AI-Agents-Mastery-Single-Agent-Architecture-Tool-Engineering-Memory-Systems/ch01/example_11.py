import time

def run_agent_benchmark(iterations: int = 1000) -> Dict[str, Any]:
    start = time.perf_counter()
    parser = RobustReActParser()
    sample = "Thought: Check status.\nAction: query_database({\"id\": 104})"
    
    for _ in range(iterations):
        step = parser.parse(sample)
        
    duration = time.perf_counter() - start
    ops_per_sec = round(iterations / duration, 2)
    p50_latency_us = round((duration / iterations) * 1e6, 2)
    
    return {
        "iterations": iterations,
        "total_time_seconds": round(duration, 4),
        "throughput_ops_per_sec": ops_per_sec,
        "latency_us_per_op": p50_latency_us
    }

print("Micro-Benchmark Results:", run_agent_benchmark(500))
