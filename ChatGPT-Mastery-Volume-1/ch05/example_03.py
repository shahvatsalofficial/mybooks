"""
Enterprise Knowledge File Chunking & Semantic Pre-Flight Validator
Target: Python 3.10+ / Tiktoken / Numpy
"""

import os
import re
import tiktoken
import numpy as np
from typing import List, Dict, Any


class KnowledgePreFlightValidator:
    def __init__(self, target_chunk_tokens: int = 1000, overlap_tokens: int = 150):
        self.tokenizer = tiktoken.get_encoding("cl100k_base") # OpenAI standard tokenizer
        self.target_chunk = target_chunk_tokens
        self.overlap = overlap_tokens

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def split_into_semantic_chunks(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Splits markdown text on heading boundaries and paragraphs with token budgeting."""
        # Split on markdown headings while retaining heading text
        sections = re.split(r'(^#{1,3}\s+.*$)', markdown_text, flags=re.MULTILINE)
        chunks = []
        current_chunk_tokens: List[int] = []
        current_chunk_text = ""
        current_heading = "Preamble"

        for part in sections:
            part = part.strip()
            if not part:
                continue

            if part.startswith('#'):
                current_heading = part
                continue

            # Process paragraphs within section
            paragraphs = part.split('\n\n')
            for p in paragraphs:
                p_text = f"[{current_heading}]\n{p}\n\n"
                p_tokens = self.tokenizer.encode(p_text)

                if len(current_chunk_tokens) + len(p_tokens) <= self.target_chunk:
                    current_chunk_tokens.extend(p_tokens)
                    current_chunk_text += p_text
                else:
                    # Flush current chunk
                    if current_chunk_text:
                        chunks.append({
                            "heading": current_heading,
                            "text": current_chunk_text.strip(),
                            "token_count": len(current_chunk_tokens)
                        })
                    # Initialize new chunk with overlap if feasible
                    overlap_slice = current_chunk_tokens[-self.overlap:] if len(current_chunk_tokens) >= self.overlap else []
                    current_chunk_tokens = overlap_slice + p_tokens
                    current_chunk_text = self.tokenizer.decode(overlap_slice) + p_text

        # Flush trailing chunk
        if current_chunk_text:
            chunks.append({
                "heading": current_heading,
                "text": current_chunk_text.strip(),
                "token_count": len(current_chunk_tokens)
            })

        return chunks

    def audit_knowledge_file(self, file_path: str) -> Dict[str, Any]:
        """Audits markdown file for token distribution, layout health, and chunk density."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Knowledge file missing at: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        total_tokens = self.count_tokens(content)
        chunks = self.split_into_semantic_chunks(content)
        chunk_sizes = [c["token_count"] for c in chunks]

        return {
            "file_path": file_path,
            "total_tokens": total_tokens,
            "total_chunks": len(chunks),
            "mean_chunk_tokens": float(np.mean(chunk_sizes)) if chunk_sizes else 0,
            "max_chunk_tokens": int(np.max(chunk_sizes)) if chunk_sizes else 0,
            "min_chunk_tokens": int(np.min(chunk_sizes)) if chunk_sizes else 0,
            "health_status": "OPTIMAL" if (total_tokens < 150000 and max(chunk_sizes) <= 1500) else "NEEDS_SPLITTING"
        }
