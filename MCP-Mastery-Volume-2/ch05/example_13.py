"""
Hierarchical Multi-Agent Supervisor Pattern with Dedicated MCP Sub-Graphs
Author: Vatsal Shah | Vatsal Shah
Runtime: Python 3.11+
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str

class RoutingDecision(BaseModel):
    """Schema for supervisor routing decision."""
    next: Literal["BILLING_AGENT", "INFRASTRUCTURE_AGENT", "FINISH"] = Field(
        ...,
        description="The specialized agent to delegate the task to, or FINISH if satisfied."
    )
    instruction: str = Field(..., description="Specific delegation context for the specialist.")

def create_supervisor_graph(billing_subgraph, infra_subgraph) -> Any:
    """Build multi-agent supervisor graph."""
    supervisor_llm = ChatOpenAI(model="gpt-4o", temperature=0.0).with_structured_output(RoutingDecision)

    async def supervisor_node(state: SupervisorState):
        decision = await supervisor_llm.ainvoke(state["messages"])
        return {"next_agent": decision.next}

    async def call_billing(state: SupervisorState):
        result = await billing_subgraph.ainvoke({"messages": state["messages"]})
        return {"messages": [result["messages"][-1]]}

    async def call_infra(state: SupervisorState):
        result = await infra_subgraph.ainvoke({"messages": state["messages"]})
        return {"messages": [result["messages"][-1]]}

    workflow = StateGraph(SupervisorState)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("billing_agent", call_billing)
    workflow.add_node("infra_agent", call_infra)

    workflow.set_entry_point("supervisor")

    def route_worker(state: SupervisorState) -> str:
        target = state.get("next_agent")
        if target == "BILLING_AGENT":
            return "billing_agent"
        if target == "INFRASTRUCTURE_AGENT":
            return "infra_agent"
        return END

    workflow.add_conditional_edges(
        "supervisor",
        route_worker,
        {
            "billing_agent": "billing_agent",
            "infra_agent": "infra_agent",
            END: END
        }
    )

    workflow.add_edge("billing_agent", "supervisor")
    workflow.add_edge("infra_agent", "supervisor")

    return workflow.compile()
