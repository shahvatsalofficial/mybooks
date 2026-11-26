@server.prompt(
    name="quarterly_risk_matrix",
    description="Filters risk-related notes and compiles a 3x3 risk assessment matrix."
)
def quarterly_risk_matrix(risk_threshold: str = "all") -> list[PromptMessage]:
    matching_notes = []
    for slug, data in NOTES_DATABASE.items():
        if "incident" in slug.lower() or "risk" in data["content"].lower():
            matching_notes.append(f"### {data['title']}\n{data['content']}")

    bundled_risks = "\n\n---\n\n".join(matching_notes) if matching_notes else "No active risk records found."

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"You are a Chief Information Security Officer. Analyze the attached organizational incident and risk records. "
                    f"Filter threshold: {risk_threshold}. Synthesize findings into a formal 3x3 risk matrix categorized by Likelihood and Impact."
                )
            )
        ),
        PromptMessage(
            role="user",
            content=EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="memo://risks/filtered_bundle.md",
                    mimeType="text/markdown",
                    text=bundled_risks
                )
            )
        )
    ]
