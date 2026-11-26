from langgraph.types import Command

class TriagedState(TypedDict):
    customer_id: str
    current_agent: str
    messages: Annotated[List[str], operator.add]
    requires_escalation: bool

def tier1_support_node(state: TriagedState) -> Command[Literal["tier2_specialist", "__end__"]]:
    """Evaluates customer inquiry and initiates dynamic handoff via Command."""
    last_msg = state["messages"][-1]
    print(f"[NODE: Tier 1] Evaluating message: '{last_msg}'")
    
    if "security vulnerability" in last_msg.lower() or "cve" in last_msg.lower():
        print("[NODE: Tier 1] Critical security alert detected! Dispatching Command handoff to Tier 2...")
        return Command(
            update={
                "current_agent": "tier2_specialist",
                "requires_escalation": True,
                "messages": ["[Tier 1 Dispatch]: Escalating directly to Security Specialist Tier 2."]
            },
            goto="tier2_specialist" # Dynamic next destination
        )
    else:
        print("[NODE: Tier 1] Routine inquiry handled. Concluding workflow.")
        return Command(
            update={
                "messages": ["[Tier 1 Dispatch]: Standard documentation provided to user."]
            },
            goto="__end__"
        )

def tier2_specialist_node(state: TriagedState) -> Command[Literal["__end__"]]:
    """Specialist node handling escalated security incidents."""
    print("[NODE: Tier 2 Specialist] Handling escalated security incident...")
    return Command(
        update={
            "messages": ["[Tier 2 Specialist]: Emergency patch applied. Security advisory logged."]
        },
        goto="__end__"
    )
