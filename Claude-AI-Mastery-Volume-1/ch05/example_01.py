"""
Enterprise Long-Context Prompt Caching Proxy
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import os
import time
import json
import logging
from typing import Generator, Dict, Any, Optional
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LongContextProxy")

class EnterpriseLongContextProxy:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.default_model = "claude-3-5-sonnet-20241022"

    def assemble_cached_payload(self, corpus_text: str, system_instructions: str) -> list:
        """
        Assembles a multi-block system prompt with an explicit 90% discount cache breakpoint.
        """
        return [
            {
                "type": "text",
                "text": system_instructions
            },
            {
                "type": "text",
                "text": f"<enterprise_corpus>\n{corpus_text}\n</enterprise_corpus>",
                "cache_control": {"type": "ephemeral"} # Cache breakpoint
            }
        ]

    def query_corpus_stream(
        self,
        corpus_text: str,
        user_query: str,
        system_instructions: str = "You are a master enterprise systems auditor. Synthesize all findings strictly from the provided corpus."
    ) -> Generator[str, None, Dict[str, Any]]:
        """
        Streams responses from Claude while monitoring prompt cache hits and token economics.
        """
        system_payload = self.assemble_cached_payload(corpus_text, system_instructions)
        start_time = time.time()
        
        telemetry = {
            "input_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
            "output_tokens": 0,
            "cache_hit_rate": 0.0,
            "latency_ms": 0,
            "estimated_cost_usd": 0.0
        }

        try:
            with self.client.messages.stream(
                model=self.default_model,
                max_tokens=4096,
                temperature=0.0,
                system=system_payload,
                messages=[{"role": "user", "content": user_query}]
            ) as stream:
                for text_delta in stream.text_stream:
                    yield text_delta

                final_message = stream.get_final_message()
                usage = final_message.usage

                telemetry["input_tokens"] = usage.input_tokens
                telemetry["cache_creation_tokens"] = getattr(usage, "cache_creation_input_tokens", 0)
                telemetry["cache_read_tokens"] = getattr(usage, "cache_read_input_tokens", 0)
                telemetry["output_tokens"] = usage.output_tokens
                telemetry["latency_ms"] = int((time.time() - start_time) * 1000)

                total_input = telemetry["input_tokens"] + telemetry["cache_read_tokens"]
                if total_input > 0:
                    telemetry["cache_hit_rate"] = round(telemetry["cache_read_tokens"] / total_input, 4)

                # Cost Calculation (Sonnet 3.5 rates)
                base_in_cost = (telemetry["input_tokens"] * 3.00) / 1_000_000
                cache_write_cost = (telemetry["cache_creation_tokens"] * 3.75) / 1_000_000
                cache_read_cost = (telemetry["cache_read_tokens"] * 0.30) / 1_000_000
                out_cost = (telemetry["output_tokens"] * 15.00) / 1_000_000
                telemetry["estimated_cost_usd"] = round(base_in_cost + cache_write_cost + cache_read_cost + out_cost, 6)

                logger.info(f"Query Telemetry: {json.dumps(telemetry)}")
                return telemetry

        except anthropic.APIError as e:
            logger.error(f"Anthropic API Exception: {str(e)}")
            raise

# Production Verification Script
if __name__ == "__main__":
    # Generate a synthetic 5,000-word corporate documentation corpus
    sample_corpus = ("# Section: Enterprise Data Retention Policy\n"
                     "All customer logs must be purged after 90 days unless an active litigation hold is flagged.\n") * 250
    
    proxy = EnterpriseLongContextProxy()
    print("Testing Enterprise Long-Context Stream with Prompt Caching...")
    
    stream_gen = proxy.query_corpus_stream(
        corpus_text=sample_corpus,
        user_query="What is the mandatory purge window for customer logs, and what is the sole exception?"
    )
    
    for chunk in stream_gen:
        print(chunk, end="", flush=True)
    print("\n[Stream Complete]")
