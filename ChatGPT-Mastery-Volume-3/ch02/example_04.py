"""
propositional_chunker.py
Enterprise Propositional Chunking Engine
Decomposes complex paragraphs into atomic, self-contained semantic propositions.
"""

import json
from typing import List
from pydantic import BaseModel, Field
from openai import AzureOpenAI


class PropositionContainer(BaseModel):
    propositions: List[str] = Field(
        description="A list of standalone, atomic factual propositions derived from the source text."
    )


class PropositionalChunker:
    def __init__(self, aoai_client: AzureOpenAI, model_deployment: str = "gpt-4o-mini"):
        self.client = aoai_client
        self.deployment = model_deployment

    def extract_propositions(self, paragraph: str) -> List[str]:
        system_instruction = (
            "You are an expert computational linguist. Deconstruct the input text into a list of "
            "independent, atomic, and factual propositions. Each proposition must be a complete sentence "
            "that can stand alone without relying on pronouns or missing antecedents. Do not omit facts, "
            "numbers, dates, or legal conditions."
        )

        completion = self.client.beta.chat.completions.parse(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Text to deconstruct:
{paragraph}"}
            ],
            response_format=PropositionContainer,
            temperature=0.0
        )

        return completion.choices[0].message.parsed.propositions


if __name__ == "__main__":
    sample_text = (
        "In Q3 2025, Acme Cloud Corp, founded by Dr. Aris Thorne in Zurich, reported a net operating "
        "income of $42.8M, representing an 18.4% increase over Q3 2024, despite experiencing severe "
        "supply chain delays in their Singapore semiconductor packaging facility."
    )
    print("Source Text:
", sample_text)
    # chunker = PropositionalChunker(...)
    # props = chunker.extract_propositions(sample_text)
    print("
Simulated Atomic Propositions:")
    print("1. Acme Cloud Corp was founded by Dr. Aris Thorne.")
    print("2. Acme Cloud Corp was founded in Zurich.")
    print("3. Acme Cloud Corp reported net operating income of $42.8M in Q3 2025.")
    print("4. Acme Cloud Corp's Q3 2025 net operating income was an 18.4% increase over Q3 2024.")
    print("5. Acme Cloud Corp experienced severe supply chain delays in their Singapore facility.")
    print("6. Acme Cloud Corp's Singapore facility is responsible for semiconductor packaging.")
