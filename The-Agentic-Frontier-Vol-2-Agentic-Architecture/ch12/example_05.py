# agent_manifest.py
"""
Agent Version Manifest — tracks all agentic artifacts with semantic versioning.
This file is committed to Git alongside agent code. Every release creates
a new version entry. Diffs between versions are reviewed in code review.
"""

AGENT_VERSION = "1.3.2"

MANIFEST = {
    "version": AGENT_VERSION,
    "release_date": "2026-08-11",
    "artifacts": {
        "system_prompt": {
            "version": "2.1.0",
            "file": "prompts/system_prompt_v2_1_0.txt",
            "sha256": "a3f7b291c84e1d20f9e8c7d6b5a4321098765432abcdef1234567890abcdef12",
            "changelog": "Added explicit instruction to cite sources in all factual claims."
        },
        "tool_schema": {
            "version": "1.4.0",
            "file": "tools/tool_schema_v1_4_0.json",
            "sha256": "b4c8d392e95f2e31ab0d7e8c6b5a32109876543cbdcef2345678901bcdef2345",
            "changelog": "Added code_runner tool. Removed deprecated search_v1 tool."
        },
        "base_llm": {
            "model": "gpt-4o",
            "provider": "openai",
            "api_version": "2024-08-01-preview",
            "changelog": "Upgraded from gpt-4-turbo. Context window: 128k."
        },
        "evaluation_golden_dataset": {
            "version": "3.2.0",
            "file": "eval/golden_dataset_v3_2_0.jsonl",
            "record_count": 847,
            "sha256": "c5d9e4a3f06c3f42bc1e8f9d7c6b4320aa87654dcefe3456789012cdef3456",
            "changelog": "Added 45 new adversarial injection test cases from Q3 security review."
        }
    },
    "eval_baseline": {
        "overall_score": 0.891,
        "accuracy": 0.902,
        "relevance": 0.888,
        "coherence": 0.915,
        "safety": 0.987,
        "measured_at": "2026-08-10T14:23:00Z",
        "sample_size": 500
    }
}
