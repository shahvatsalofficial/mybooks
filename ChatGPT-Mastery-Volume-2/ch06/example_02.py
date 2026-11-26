"""
Production Model Distillation Benchmark Suite
Evaluates syntax accuracy, schema compliance, and latency across base and fine-tuned models.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
import json
import asyncio
from typing import List, Dict, Any
from openai import AsyncOpenAI

client = AsyncOpenAI()

TEST_CASES = [
    {
        "prompt": "Extract portfolio asset allocation: $50k in US Equities, $20k in Municipal Bonds, $10k in Gold.",
        "expected_keys": ["us_equities", "municipal_bonds", "gold"]
    },
    {
        "prompt": "Extract portfolio asset allocation: 100k in Real Estate REITs, 40k in Treasury Bills.",
        "expected_keys": ["real_estate_reits", "treasury_bills"]
    }
]

async def benchmark_model(model_id: str, test_suite: List[Dict[str, Any]]) -> Dict[str, Any]:
    print(f"\nEvaluating Model: {model_id}...")
    total_latency = 0.0
    valid_syntax_count = 0
    total_tokens = 0

    for test in test_suite:
        start_time = time.perf_counter()
        try:
            res = await client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a financial asset extractor. Output strict JSON."},
                    {"role": "user", "content": test["prompt"]}
                ],
                temperature=0.0
            )
            duration = time.perf_counter() - start_time
            total_latency += duration
            total_tokens += res.usage.total_tokens

            # Audit JSON syntax and expected keys
            raw_text = res.choices[0].message.content
            parsed = json.loads(raw_text)
            
            has_all_keys = all(k in parsed for k in test["expected_keys"])
            if has_all_keys:
                valid_syntax_count += 1

        except Exception as e:
            print(f"   ⚠️ Test failure on prompt: {e}")

    avg_latency = (total_latency / len(test_suite)) * 1000.0
    accuracy = (valid_syntax_count / len(test_suite)) * 100.0

    return {
        "model": model_id,
        "accuracy_pct": accuracy,
        "avg_latency_ms": avg_latency,
        "total_tokens": total_tokens
    }

async def run_distillation_comparison():
    print("=======================================================")
    print("🎯 RUNNING DISTILLATION COMPARATIVE BENCHMARK")
    print("=======================================================")

    teacher = "gpt-4o"
    base_student = "gpt-4o-mini"
    fine_tuned_student = "ft:gpt-4o-mini-2024-07-18:enterprise-org:fin-support-v2:xyz99"

    # In production: evaluate across models
    models_to_test = [teacher, base_student]
    results = []

    for m in models_to_test:
        metrics = await benchmark_model(m, TEST_CASES)
        results.append(metrics)
        print(f"   Accuracy: {metrics['accuracy_pct']:.1f}% | Avg Latency: {metrics['avg_latency_ms']:.1f}ms")

    print("\n✅ Benchmark Completed!")

if __name__ == "__main__":
    asyncio.run(run_distillation_comparison())
