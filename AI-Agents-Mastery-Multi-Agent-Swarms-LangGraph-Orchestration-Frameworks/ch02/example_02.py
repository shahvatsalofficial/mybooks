def researcher_node(state: ResearchGraphState) -> Dict[str, Any]:
    """Generates or revises content based on audit feedback."""
    rev = state.get("revision_count", 0) + 1
    notes = state.get("audit_notes", [])
    
    print(f"\n[NODE: Researcher] Executing Turn {rev} for topic: '{state['topic']}'")
    
    if not notes:
        # Initial Draft
        draft = (
            f"Technical Brief on {state['topic']}:\n"
            "- Core Concept: Distributed state graphs provide deterministic cyclic orchestration.\n"
            "- Implementation: Use Redis for checkpointing."
        )
    else:
        # Iterative Revision based on critique
        last_feedback = notes[-1]
        print(f"[NODE: Researcher] Incorporating Critique: {last_feedback}")
        draft = (
            f"Technical Brief on {state['topic']} (Revised - Turn {rev}):\n"
            "- Core Concept: Distributed state graphs provide deterministic cyclic orchestration.\n"
            "- Implementation: Use Redis Checkpointer with distributed locking.\n"
            "- Security Gate: Enforce TLS 1.3 encryption and mutual auth."
        )
        
    return {
        "draft_content": draft,
        "revision_count": rev
    }

def auditor_node(state: ResearchGraphState) -> Dict[str, Any]:
    """Audits draft content against strict production security standards."""
    draft = state["draft_content"]
    rev = state["revision_count"]
    print(f"[NODE: Auditor] Inspecting Draft Revision {rev}...")
    
    # Audit Rule: Must explicitly specify TLS 1.3 and mutual auth
    if "TLS 1.3" in draft and "mutual auth" in draft:
        print("[NODE: Auditor] PASS: Draft satisfies all enterprise security benchmarks.")
        return {
            "audit_notes": [f"Turn {rev}: APPROVED - Security criteria satisfied."],
            "is_approved": True,
            "final_output": draft
        }
    else:
        print("[NODE: Auditor] REJECT: Missing mandatory transport security and mutual auth specs.")
        return {
            "audit_notes": [f"Turn {rev}: REJECTED - Must explicitly specify TLS 1.3 and mutual auth."],
            "is_approved": False
        }
