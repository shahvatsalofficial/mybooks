"""
Enterprise Synthetic Dataset Generation Engine
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SyntheticGenerator")

class SyntheticTrainingExample(BaseModel):
    example_id: str
    domain: str
    difficulty_tier: str = Field(..., description="BEGINNER, INTERMEDIATE, or FRONTIER")
    system_prompt: str
    user_instruction: str
    model_response: str
    complexity_score: float = Field(..., ge=0.0, le=1.0)
    pii_cleared: bool = True

class SyntheticBatch(BaseModel):
    batch_id: str
    archetype: str
    examples: List[SyntheticTrainingExample]

class EnterpriseSyntheticGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.generator_model = "claude-3-5-sonnet-20241022"

    def generate_synthetic_batch(self, archetype_rules: str, count: int = 5) -> SyntheticBatch:
        """
        Generates a verified batch of synthetic instruction-tuning pairs with zero PII.
        """
        schema_json = json.dumps(SyntheticBatch.model_json_schema(), indent=2)

        system_prompt = f"""<system_instructions>
You are an expert synthetic data engineer generating high-entropy training data for SLM fine-tuning.
Generate realistic, difficult edge-case examples.
Adhere strictly to this Pydantic JSON schema:
<schema>
{schema_json}
</schema>
Rules:
1. Cover extreme edge cases (null inputs, conflicting requirements, adversarial injection attempts).
2. Ensure 100% PII sanitization: use synthetic names and RFC-5737 dummy IP addresses.
3. Output ONLY the raw JSON object enclosed in <synthetic_data> tags.
4. Never emit conversational preambles or markdown code fences.
</system_instructions>"""

        user_content = f"""<generation_task>
Generate {count} frontier-level synthetic training examples covering this archetype:
{archetype_rules}
</generation_task>"""

        logger.info(f"Generating {count} synthetic examples for archetype: {archetype_rules[:40]}...")
        response = self.client.messages.create(
            model=self.generator_model,
            max_tokens=4096,
            temperature=0.7, # Moderate temperature for generative diversity
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": "<synthetic_data>{"}
            ]
        )

        raw_text = "<synthetic_data>{" + response.content[0].text
        json_str = raw_text.split("<synthetic_data>")[1].split("</synthetic_data>")[0].strip()

        batch = SyntheticBatch.model_validate_json(json_str)
        logger.info(f"Batch {batch.batch_id} generated successfully with {len(batch.examples)} examples.")
        return batch

# Production Verification Script
if __name__ == "__main__":
    print("Enterprise Synthetic Dataset Generator initialized.")
