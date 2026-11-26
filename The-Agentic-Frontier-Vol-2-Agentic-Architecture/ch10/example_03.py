# evaluation/synthetic_dataset_generator.py
"""
Enterprise Synthetic Golden Dataset Generator using Evol-Instruct.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import json
from typing import List, Dict
from pydantic import BaseModel, Field
import openai

class SyntheticTestCase(BaseModel):
    id: str
    original_prompt: str
    evolved_prompt: str
    evolution_type: str
    expected_tools: List[str]
    ground_truth: str

EVOLUTION_PROMPTS = {
    "add_constraints": "Rewrite the question to include strict operational constraints (e.g., specific date ranges, budget limits, or compliance rules).",
    "deepen_reasoning": "Transform this simple query into a multi-step analytical prompt requiring comparisons and root-cause analysis.",
    "multi_tool": "Modify the prompt so that answering it requires querying both a relational SQL database and an un-structured vector store."
}

def evolve_question(base_text: str, evolution_type: str, client: openai.OpenAI) -> Dict[str, str]:
    instruction = EVOLUTION_PROMPTS.get(evolution_type, "Make the question more complex.")
    prompt = f"""
You are an expert AI Benchmark Engineer.
Take the following context and base question, and rewrite it according to this evolution rule: {instruction}

[Base Context]:
{base_text}

Output JSON with keys: 'evolved_prompt', 'ground_truth', 'expected_tools' (list of tool names).
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)
