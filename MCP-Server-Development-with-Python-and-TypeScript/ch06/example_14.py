"""
notes_mcp_server.py
The Complete Spine Project — Full Python FastMCP Production Implementation.
"""

import sys
import re
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, List
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import PromptMessage, TextContent, EmbeddedResource, TextResourceContents
from pydantic import BaseModel, Field, field_validator

DB_FILE = "notes_storage.db"


# ─── LIFESPAN RESOURCE POOLING ────────────────────────────────────────────────
@asynccontextmanager
async def notes_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manages database connection pool and schema initialization."""
    sys.stderr.write("[Lifespan] Initializing notes-mcp SQLite storage...\n")
    db = await aiosqlite.connect(DB_FILE)
    db.row_factory = aiosqlite.Row

    # Initialize relational schema
    await db.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    try:
        yield {"db": db}
    finally:
        sys.stderr.write("[Lifespan] Closing SQLite storage...\n")
        await db.close()


mcp = FastMCP("notes-mcp", lifespan=notes_lifespan)


# ─── PYDANTIC SCHEMAS ──────────────────────────────────────────────────────────
class CreateNoteInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=120, description="Title of the note.")
    content: str = Field(..., min_length=1, description="Markdown body content.")
    tags: Optional[List[str]] = Field(default=[], description="List of category tags.")

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Title cannot be blank or whitespace only.")
        return cleaned


class SearchNotesInput(BaseModel):
    query: str = Field(..., min_length=1, description="Search term matching title or content.")
    tag_filter: Optional[str] = Field(None, description="Optional tag filter.")


def slugify(text: str) -> str:
    """Converts a title into a URL-safe unique slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")


# ─── TOOLS PRIMITIVES ──────────────────────────────────────────────────────────
@mcp.tool()
async def create_or_update_note(note: CreateNoteInput, ctx: Context) -> str:
    """Creates a new note or updates an existing note matching the derived slug."""
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]
    slug = slugify(note.title)
    tags_str = ",".join([t.strip().lower() for t in note.tags if t.strip()])

    sys.stderr.write(f"[Tools] Persisting note '{slug}'...\n")
    await db.execute("""
        INSERT INTO notes (slug, title, content, tags, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title,
            content=excluded.content,
            tags=excluded.tags,
            updated_at=CURRENT_TIMESTAMP
    """, (slug, note.title, note.content, tags_str))
    await db.commit()

    return f"Note successfully saved. URI: memo://notes/{slug}"


@mcp.tool()
async def search_notes(params: SearchNotesInput, ctx: Context) -> str:
    """Searches stored notes by keyword and optional tag filter."""
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]
    sys.stderr.write(f"[Tools] Searching notes for query: '{params.query}'...\n")

    sql = "SELECT slug, title, SUBSTR(content, 1, 120) AS preview, tags FROM notes WHERE (title LIKE ? OR content LIKE ?)"
    bindings = [f"%{params.query}%", f"%{params.query}%"]

    if params.tag_filter:
        sql += " AND tags LIKE ?"
        bindings.append(f"%{params.tag_filter.lower()}%")

    sql += " ORDER BY updated_at DESC LIMIT 10"

    async with db.execute(sql, bindings) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        return f"No notes found matching query '{params.query}'."

    results = []
    for r in rows:
        results.append(f"• **{r['title']}** (`memo://notes/{r['slug']}`)\n  Tags: [{r['tags']}]\n  Preview: {r['preview']}...")

    return "\n\n".join(results)


# ─── RESOURCES PRIMITIVES ──────────────────────────────────────────────────────
@mcp.resource("memo://notes/{slug}")
async def read_note_resource(slug: str, ctx: Context) -> str:
    """Exposes a specific note's full markdown content as a read-only resource."""
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]
    sys.stderr.write(f"[Resources] Fetching resource memo://notes/{slug}...\n")

    async with db.execute("SELECT title, content, tags, updated_at FROM notes WHERE slug = ?", (slug,)) as cursor:
        row = await cursor.fetchone()

    if not row:
        raise KeyError(f"Note with slug '{slug}' does not exist.")

    return f"# {row['title']}\n\n*Last Updated: {row['updated_at']} | Tags: {row['tags']}*\n\n{row['content']}"


# ─── PROMPTS PRIMITIVES ────────────────────────────────────────────────────────
@mcp.prompt()
async def synthesize_all_notes(target_audience: str = "Engineering Team", ctx: Context = None) -> list[PromptMessage]:
    """Generates an executive briefing prompt embedding all notes currently stored."""
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]
    async with db.execute("SELECT title, content FROM notes ORDER BY updated_at DESC LIMIT 20") as cursor:
        rows = await cursor.fetchall()

    if not rows:
        bundled_text = "No notes currently stored in system."
    else:
        bundled_text = "\n\n---\n\n".join([f"## {r['title']}\n{r['content']}" for r in rows])

    msg_instruction = PromptMessage(
        role="user",
        content=TextContent(
            type="text",
            text=(
                f"You are a Principal Technical Program Manager. "
                f"Review the attached knowledge base notes and generate an executive summary tailored for {target_audience}.\n"
                "Extract top strategic priorities, technical blockers, and critical deadlines."
            )
        )
    )

    msg_context = PromptMessage(
        role="user",
        content=EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri="memo://notes/consolidated_briefing",
                mimeType="text/markdown",
                text=bundled_text
            )
        )
    )

    return [msg_instruction, msg_context]


if __name__ == "__main__":
    mcp.run(transport="stdio")
