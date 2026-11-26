import json
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

# 1. Define Strict Pydantic Tool Schemas
class QueryDatabaseArgs(BaseModel):
    table: str = Field(description="Target table name (e.g., customers, orders, refunds)")
    filter_key: str = Field(description="Column to filter on")
    filter_value: str = Field(description="Exact value to match")

class IssueRefundArgs(BaseModel):
    order_id: str = Field(description="The unique order identifier (e.g., ORD-9912)")
    amount_cents: int = Field(gt=0, le=100000, description="Refund amount in integer cents")
    reason: str = Field(min_length=5, description="Auditable justification for refund")

# 2. Mock Operational Environment
DATABASE_MOCK = {
    "orders": [
        {"order_id": "ORD-9912", "customer_id": "CUST-104", "amount_cents": 4500, "status": "delivered"},
        {"order_id": "ORD-8821", "customer_id": "CUST-202", "amount_cents": 12000, "status": "processing"}
    ],
    "customers": [
        {"customer_id": "CUST-104", "name": "Elena Rostova", "tier": "enterprise", "email": "elena@acme.corp"}
    ]
}

def tool_query_db(table: str, filter_key: str, filter_value: str) -> str:
    rows = DATABASE_MOCK.get(table, [])
    results = [r for r in rows if str(r.get(filter_key)) == str(filter_value)]
    return json.dumps(results if results else {"error": "No matching records found."})

def tool_issue_refund(order_id: str, amount_cents: int, reason: str) -> str:
    for order in DATABASE_MOCK["orders"]:
        if order["order_id"] == order_id:
            order["status"] = "refunded"
            return json.dumps({"status": "success", "tx_id": f"TX-REF-{order_id}", "refunded_cents": amount_cents})
    return json.dumps({"error": f"Order {order_id} not found."})

# 3. Tool Dispatch Gateway
TOOL_REGISTRY: Dict[str, Tuple[Callable, type[BaseModel]]] = {
    "query_database": (tool_query_db, QueryDatabaseArgs),
    "issue_refund": (tool_issue_refund, IssueRefundArgs)
}

def execute_tool(tool_name: str, raw_arguments_json: str) -> str:
    if tool_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Tool '{tool_name}' does not exist in registry."})
    
    func, schema_cls = TOOL_REGISTRY[tool_name]
    try:
        parsed_dict = json.loads(raw_arguments_json)
        validated_args = schema_cls(**parsed_dict)
        return func(**validated_args.model_dump())
    except Exception as e:
        return json.dumps({"validation_error": str(e), "expected_schema": schema_cls.model_json_schema()})

# 4. Deterministic Single-Agent Reasoning Loop
SYSTEM_PROMPT = """You are an Autonomous Customer Operations Agent.
Solve the user's objective using this strict thought loop:

Thought: Analyze the state and decide what to do next.
Action: tool_name({"arg": "val"})
Observation: [The system will supply the tool output here]
... (repeat Thought/Action/Observation as needed)
Thought: I now have the final answer.
Final Answer: Complete, structured resolution to the user.

Available Tools:
- query_database({"table": str, "filter_key": str, "filter_value": str})
- issue_refund({"order_id": str, "amount_cents": int, "reason": str})
"""

def parse_agent_output(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    thought_match = re.search(r"Thought:s*(.*?)(?=
Action:|
Final Answer:|$)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else None
    
    final_match = re.search(r"Final Answer:s*(.*)", text, re.DOTALL)
    if final_match:
        return thought, None, final_match.group(1).strip()
    
    action_match = re.search(r"Action:s*(w+)((.*))", text, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        args_str = action_match.group(2).strip()
        return thought, tool_name, args_str
    
    return thought, None, None
