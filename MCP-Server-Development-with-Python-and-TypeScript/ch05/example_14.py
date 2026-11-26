"""
notes_prompts_server.py
The Spine Project — Phase 3: Standardized Prompts for notes-mcp.
"""

import json
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent, EmbeddedResource, TextResourceContents

server = FastMCP("notes-mcp-prompts")

# Reference notes database from earlier chapters
NOTES_DATABASE = {
    "q3_roadmap": {
        "title": "Q3 Engineering Roadmap",
        "content": "# Q3 Roadmap\n- Migrate 40 microservices to MCP architecture.\n- Cut LLM API costs by 35% using semantic caching.\n- Zero P0 incidents target."
    },
    "infra_incident": {
        "title": "Incident Retrospective: Redis Outage",
        "content": "# Redis Outage Retrospective\n- Root Cause: Maxclients ceiling reached.\n- Action Item: Deploy Redis Sentinel cluster."
    }
}


@server.prompt(
    name="summarize_notes",
    description="Assembles all active project notes into an executive synthesis prompt."
)
def summarize_notes(target_audience: str = "engineering_leadership") -> list[PromptMessage]:
    """Generates an executive briefing prompt embedding all notes."""
    # Serialize all active notes as an embedded resource
    bundled_notes = "\n\n---\n\n".join([
        f"## {data['title']}\n{data['content']}"
        for data in NOTES_DATABASE.values()
    ])

    msg_instruction = PromptMessage(
        role="user",
        content=TextContent(
            type="text",
            text=(
                f"You are a Strategic Technical Program Manager. "
                f"Synthesize the attached project notes into an executive briefing tailored for {target_audience}.\n"
                "Highlight active risks, resourcing bottlenecks, and upcoming milestones."
            )
        )
    )

    msg_context = PromptMessage(
        role="user",
        content=EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri="memo://notes/consolidated_bundle.md",
                mimeType="text/markdown",
                text=bundled_notes
            )
        )
    )

    return [msg_instruction, msg_context]


@server.prompt(
    name="action_items_extractor",
    description="Extract actionable checklists from a designated note."
)
def action_items_extractor(note_slug: str) -> list[PromptMessage]:
    """Generates a checklist extraction prompt for a single note."""
    if note_slug not in NOTES_DATABASE:
        raise KeyError(f"Note '{note_slug}' does not exist.")

    note = NOTES_DATABASE[note_slug]
    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Extract all action items, assignees, and target dates from the following note into a GitHub-style markdown task list:\n\n{note['content']}"
            )
        )
    ]


if __name__ == "__main__":
    server.run(transport="stdio")
