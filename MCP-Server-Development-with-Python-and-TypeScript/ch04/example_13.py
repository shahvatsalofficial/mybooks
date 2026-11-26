"""
notes_tools_server.py
The Spine Project — Phase 2: Mutation & Search Tools for notes-mcp.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

server = FastMCP("notes-mcp-tools")

# In-memory storage shared across project
NOTES_DATABASE: Dict[str, Dict[str, Any]] = {}


class CreateNoteInput(BaseModel):
    slug: str = Field(
        ...,
        pattern=r"^[a-z0-9_-]+$",
        description="Unique URL-safe lowercase slug for the note (e.g. 'project-phoenix')."
    )
    title: str = Field(..., min_length=1, max_length=120, description="Human-readable title.")
    content: str = Field(..., min_length=1, description="Markdown body content.")
    tags: List[str] = Field(default_factory=list, description="Array of topical tags.")


class AppendNoteInput(BaseModel):
    slug: str = Field(..., description="Target note slug to append to.")
    text: str = Field(..., min_length=1, description="Markdown content to append.")


@server.tool(
    name="create_note",
    description="Create a new markdown note with metadata tags. Rejects existing slugs."
)
def create_note(params: CreateNoteInput) -> str:
    """Creates a new note, enforcing slug uniqueness."""
    if params.slug in NOTES_DATABASE:
        return f"Error: Note with slug '{params.slug}' already exists. Use append_note or choose a new slug."

    now = datetime.now(timezone.utc).isoformat()
    NOTES_DATABASE[params.slug] = {
        "title": params.title,
        "content": params.content,
        "tags": params.tags,
        "created_at": now,
        "updated_at": now,
    }

    return f"Success: Created note '{params.slug}' with {len(params.content)} characters."


@server.tool(
    name="append_note",
    description="Append markdown text to an existing note."
)
def append_note(params: AppendNoteInput) -> str:
    """Appends content to an existing note."""
    if params.slug not in NOTES_DATABASE:
        return f"Error: Note '{params.slug}' not found. Cannot append."

    note = NOTES_DATABASE[params.slug]
    note["content"] += f"\n\n{params.text}"
    note["updated_at"] = datetime.now(timezone.utc).isoformat()

    return f"Success: Appended {len(params.text)} characters to '{params.slug}'."


@server.tool(
    name="search_notes",
    description="Search notes by keyword in title, body, or tags."
)
def search_notes(query: str) -> str:
    """Performs case-insensitive substring search across notes."""
    q = query.lower()
    matches = []

    for slug, note in NOTES_DATABASE.items():
        if (q in slug or
            q in note["title"].lower() or
            q in note["content"].lower() or
            any(q in tag.lower() for tag in note["tags"])):
            matches.append({
                "slug": slug,
                "title": note["title"],
                "tags": note["tags"],
                "preview": note["content"][:100] + "..."
            })

    return json.dumps(matches, indent=2)


if __name__ == "__main__":
    server.run(transport="stdio")
