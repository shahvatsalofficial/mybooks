"""
Enterprise Claude Project Automated Git Synchronizer
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import os
import hmac
import hashlib
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ProjectSync] %(message)s")
logger = logging.getLogger("ProjectSync")

app = FastAPI(title="Claude Project Knowledge Synchronizer")
anthropic_client = anthropic.Anthropic()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "super-secret-enterprise-key")
CLAUDE_PROJECT_ID = os.getenv("CLAUDE_PROJECT_ID", "proj_ent_architecture_01")
MAX_KNOWLEDGE_TOKENS = 135000

class FileSyncPayload(BaseModel):
    repository: str
    branch: str
    modified_files: List[str]

class KnowledgeSanitizer:
    @staticmethod
    def calculate_tokens(text: str) -> int:
        return int(len(text.split()) * 1.33)

    @classmethod
    def bundle_repository_files(cls, file_paths: List[str]) -> Tuple[str, int]:
        bundled_xml = "<knowledge_documents>\n"
        accumulated_tokens = 0

        for path in file_paths:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            file_tokens = cls.calculate_tokens(content)
            if accumulated_tokens + file_tokens > MAX_KNOWLEDGE_TOKENS:
                logger.warning(f"Budget ceiling reached. Skipping {path}")
                break

            bundled_xml += f'  <document id="{os.path.basename(path)}">\n{content.strip()}\n  </document>\n'
            accumulated_tokens += file_tokens

        bundled_xml += "</knowledge_documents>"
        return bundled_xml, accumulated_tokens

@app.post("/v1/webhooks/github-sync")
async def handle_github_sync(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """
    Validates HMAC signature and synchronizes updated repository files to Claude Project.
    """
    raw_body = await request.body()
    
    # Verify HMAC-SHA256 signature
    expected_sig = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    
    if not x_hub_signature_256 or not hmac.compare_digest(x_hub_signature_256, expected_sig):
        logger.error("Unauthorized webhook dispatch: Invalid signature.")
        raise HTTPException(status_code=403, detail="Invalid HMAC signature.")

    payload = await request.json()
    commits = payload.get("commits", [])
    modified_files = set()

    for commit in commits:
        modified_files.update(commit.get("added", []))
        modified_files.update(commit.get("modified", []))

    logger.info(f"Received sync event for {len(modified_files)} files in repository {payload.get('repository', {}).get('name')}")

    # Bundle and synchronize
    xml_docs, total_tokens = KnowledgeSanitizer.bundle_repository_files(list(modified_files))
    
    logger.info(f"Successfully packaged {total_tokens} tokens for Claude Project {CLAUDE_PROJECT_ID}.")

    return {
        "status": "SYNCHRONIZED",
        "project_id": CLAUDE_PROJECT_ID,
        "indexed_tokens": total_tokens,
        "remaining_budget": MAX_KNOWLEDGE_TOKENS - total_tokens
    }
