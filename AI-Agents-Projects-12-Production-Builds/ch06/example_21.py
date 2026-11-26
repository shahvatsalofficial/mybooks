from __future__ import annotations


def render_outreach_with_fallback(
    first_name: str,
    company_name: str,
    llm_draft: str,
    ungrounded_claims: list[str],
) -> tuple[str, bool]:
    if not ungrounded_claims:
        return llm_draft, False
    safe_template = (
        f"Hi {first_name}, thanks for exploring our platform for {company_name}. "
        f"Would you like a 15-minute architecture walkthrough with our solutions team this week?"
    )
    return safe_template, True


if __name__ == "__main__":
    body, used_fallback = render_outreach_with_fallback(
        first_name="Priya",
        company_name="Acme Cloud Ltd",
        llm_draft="Congrats on your $45M Series C!",
        ungrounded_claims=["$45M", "Series C"],
    )
    print(f"used_fallback={used_fallback} -> {body}")
