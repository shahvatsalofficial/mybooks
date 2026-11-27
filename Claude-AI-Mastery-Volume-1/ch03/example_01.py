"""
Enterprise Claude Project Synchronizer & Token Auditor
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import os
import sys
import glob
from typing import List, Dict, Tuple

class ClaudeProjectSynchronizer:
    """
    Automated tool for bundling, token budgeting, and packaging
    local codebases into Claude Project knowledge files.
    """
    def __init__(self, max_token_budget: int = 120000):
        self.max_token_budget = max_token_budget
        self.supported_extensions = ['.py', '.ts', '.js', '.md', '.json', '.sql', '.yaml']

    def estimate_tokens(self, text: str) -> int:
        """Heuristic BPE token estimator (~1.3 tokens per whitespace-delimited word)."""
        return int(len(text.split()) * 1.33)

    def scan_and_bundle_directory(self, root_dir: str) -> Tuple[str, Dict[str, Any]]:
        bundled_xml = "<project_knowledge_base>\n"
        manifest = {}
        total_tokens = 0
        total_files = 0

        for ext in self.supported_extensions:
            pattern = os.path.join(root_dir, f"**/*{ext}")
            for file_path in glob.glob(pattern, recursive=True):
                # Ignore build and dependency directories
                if any(ignored in file_path for ignored in ['node_modules', '.git', 'dist', '__pycache__', 'venv']):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    file_tokens = self.estimate_tokens(content)
                    
                    if total_tokens + file_tokens > self.max_token_budget:
                        print(f"⚠️ Warning: Token budget reached. Skipping {file_path}")
                        continue

                    rel_path = os.path.relpath(file_path, root_dir)
                    bundled_xml += f'  <document path="{rel_path}">\n{content.strip()}\n  </document>\n'
                    manifest[rel_path] = file_tokens
                    total_tokens += file_tokens
                    total_files += 1

                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")

        bundled_xml += "</project_knowledge_base>"
        
        telemetry = {
            "total_files_indexed": total_files,
            "total_tokens_estimated": total_tokens,
            "budget_utilization_pct": round((total_tokens / self.max_token_budget) * 100, 2)
        }

        return bundled_xml, telemetry

if __name__ == "__main__":
    syncer = ClaudeProjectSynchronizer()
    print("Scanning local directory for Claude Project packaging...")
    xml_payload, report = syncer.scan_and_bundle_directory(".")
    print(f"✅ Packaged {report['total_files_indexed']} files ({report['total_tokens_estimated']} tokens).")
    print(f"   Budget Utilization: {report['budget_utilization_pct']}% of {syncer.max_token_budget} limit.")
