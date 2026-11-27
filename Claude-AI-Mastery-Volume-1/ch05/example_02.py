"""
Enterprise Long-Document Compaction & Token Budgeting Engine
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import re
import logging
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CompactionEngine")

class DocumentCompactor:
    def __init__(self, target_token_ceiling: int = 150000):
        self.target_token_ceiling = target_token_ceiling

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) / 3.8)

    def calculate_sid_score(self, paragraph: str) -> float:
        # Count numbers, capital entities, and operative verbs
        words = paragraph.split()
        if not words:
            return 0.0
        
        entities = len(re.findall(r"\b[A-Z][a-z]+\b", paragraph))
        numbers = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", paragraph))
        obligations = len(re.findall(r"\b(?:shall|must|agrees|warrants|represents|indemnifies)\b", paragraph, re.IGNORECASE))
        
        score = (entities + (numbers * 1.5) + (obligations * 2.0)) / len(words)
        return score

    def compact_corpus(self, raw_corpus: str) -> str:
        current_tokens = self.estimate_tokens(raw_corpus)
        logger.info(f"Raw Corpus Tokens: {current_tokens}")
        
        if current_tokens <= self.target_token_ceiling:
            logger.info("Corpus fits within target token ceiling. No compaction required.")
            return raw_corpus

        paragraphs = raw_corpus.split("\n\n")
        scored_paragraphs = []

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            # Always preserve headers and code blocks
            if p_clean.startswith("#") or p_clean.startswith("```"):
                scored_paragraphs.append((p_clean, 999.0))
            else:
                score = self.calculate_sid_score(p_clean)
                scored_paragraphs.append((p_clean, score))

        # Sort non-essential paragraphs by SID score and prune low-density noise
        threshold = 0.08
        pruned_paragraphs = [p for p, score in scored_paragraphs if score >= threshold]
        compacted_text = "\n\n".join(pruned_paragraphs)
        
        compacted_tokens = self.estimate_tokens(compacted_text)
        logger.info(f"Compacted Tokens: {compacted_tokens} (Slashing {current_tokens - compacted_tokens} tokens).")
        return compacted_text
