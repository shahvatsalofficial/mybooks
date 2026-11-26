"""
notes_resource_server.py
The Spine Project — Phase 1: Resource Subsystem for notes-mcp.
Exposes a dynamic markdown notes library with full subscription capabilities.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

# Initialize Spine Project Server
server = FastMCP("notes-mcp")

NOTES_STORE: Dict[str, Dict[str, Any]] = {
    "architecture": {
        "title": "System Architecture",
        "tags": ["design", "infra"],
        "content": "# System Architecture\n\nMCP serves as the primary context bridge.",
        "modified_at": "2026-10-23T10:00:00Z"
    },
    "guidelines": {
        "title": "Coding Guidelines",
        "tags": ["engineering", "python"],
        "content": "# Coding Guidelines\n\nAlways enforce strict typing and non-blocking I/O.",
        "modified_at": "2026-10-23T10:15:00Z"
    }
}


# 1. Expose the Index Resource
@server.resource("memo://notes/index")
def get_notes_index() -> str:
    """Returns a JSON summary of all available notes in the repository."""
    summary = [
        {
            "id": note_id,
            "title": data["title"],
            "tags": data["tags"],
            "modified_at": data["modified_at"]
        }
        for note_id, data in NOTES_STORE.items()
    ]
    return json.dumps(summary, indent=2)


# 2. Expose the Dynamic Note Template
@server.resource("memo://notes/{note_id}")
def get_individual_note(note_id: str) -> str:
    """Fetch the full markdown content of a specific note by ID."""
    if note_id not in NOTES_STORE:
        raise KeyError(f"Note '{note_id}' does not exist in store.")
    
    note = NOTES_STORE[note_id]
    # Inlined frontmatter metadata + content
    header = f"---\ntitle: {note['title']}\ntags: {', '.join(note['tags'])}\n---\n\n"
    return header + note["content"]


if __name__ == "__main__":
    # Standard stdio execution
    server.run(transport="stdio")
