"""
Production LangGraph ReAct StateGraph with Human-in-the-Loop Interrupts
Author: Vatsal Shah | Vatsal Shah
Runtime: Python 3.11+
"""

import operator
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    """Global state of the agent workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    action_risk_level: str

def should_continue(state: AgentState) -> str:
    """Evaluate whether the agent desires tool execution or final response."""
    messages = state["messages"]
    last_message = messages[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return "end"

    # Inspect tool call for high-risk operations
    for tc in last_message.tool_calls:
        if "delete" in tc["name"] or "refund" in tc["name"] or "drop" in tc["name"]:
            return "require_approval"

    return "execute_tools"

def build_production_graph(tools: List[Any], checkpointer=None) -> Any:
    """Compile and return runnable StateGraph."""
    model = ChatOpenAI(model="gpt-4o", temperature=0.0).bind_tools(tools)

    # 1. Define Nodes
    async def agent_node(state: AgentState):
        response = await model.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    # 2. Construct Graph Workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")

    # 3. Add Conditional Routing Edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "execute_tools": "tools",
            "require_approval": "tools",  # Can be interrupted before entering
            "end": END
        }
    )

    # Tool execution always loops back to agent to evaluate response
    workflow.add_edge("tools", "agent")

    # 4. Compile with Checkpointer and Interrupt
    cp = checkpointer or MemorySaver()
    app = workflow.compile(
        checkpointer=cp,
        interrupt_before=["tools"]  # Pauses if condition routed to approval
    )
    return app
