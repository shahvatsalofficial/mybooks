"""
Recipe 02.4: Autonomous Self-Healing Tool Loop
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import json
from typing import List, Dict, Any
import anthropic

class SelfHealingDatabaseAgent:
    def __init__(self, max_repair_attempts: int = 3):
        self.client = anthropic.Anthropic()
        self.max_repair_attempts = max_repair_attempts

    def execute_sql_safeguard(self, query: str) -> str:
        # Mock database engine enforcing strict table validation
        valid_tables = ["customers", "invoices", "payments"]
        for table in valid_tables:
            if table in query.lower():
                return json.dumps({"status": "SUCCESS", "rows": [{"id": 101, "total": 450.00}]})
        raise ValueError(f"Query targets invalid table. Valid schema tables are: {valid_tables}")

    def run_self_healing_query(self, user_prompt: str) -> str:
        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_prompt}]
        tools = [{
            "name": "run_analytics_query",
            "description": "Executes SQL query on analytics warehouse.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }]

        repair_count = 0
        while repair_count < self.max_repair_attempts:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                tools=tools,
                messages=messages
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join([b.text for b in response.content if hasattr(b, 'text')])

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        sql_arg = block.input.get("query", "")
                        result_data = self.execute_sql_safeguard(sql_arg)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_data,
                            "is_error": False
                        })
                    except Exception as err:
                        repair_count += 1
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Execution Error: {str(err)}. Please review the valid schema and correct your SQL query.",
                            "is_error": True
                        })

            messages.append({"role": "user", "content": tool_results})

        raise RuntimeError("Agent exceeded maximum self-repair attempts without resolving schema errors.")
