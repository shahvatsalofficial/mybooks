# resilient_dispatcher.py
import json
from typing import Dict, Any, List
from pydantic import ValidationError

class ResilientToolDispatcher:
    def __init__(self, registry):
        self.registry = registry

    def dispatch_with_self_repair(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = tool_call.get("name")
        raw_args_str = tool_call.get("arguments", "{}")
        
        # Step 1: Validate raw JSON syntax
        try:
            parsed_args = json.loads(raw_args_str)
        except json.JSONDecodeError as err:
            return {
                "status": "ERROR_NEEDS_RETRY",
                "feedback": (
                    f"JSONDecodeError: Tool call argument was not valid JSON. Detail: {str(err)}. "
                    "Resend tool call with valid JSON syntax."
                )
            }

        # Step 2: Execute tool with schema and exception isolation
        try:
            result = self.registry.execute(tool_name, parsed_args)
            return {
                "status": "SUCCESS",
                "tool_name": tool_name,
                "result": result
            }
        except TypeError as err:
            return {
                "status": "ERROR_NEEDS_RETRY",
                "feedback": (
                    f"ParameterTypeError: Failed to invoke '{tool_name}'. Details: {str(err)}. "
                    "Verify the parameter names and types in the schema and resend."
                )
            }
        except Exception as err:
            return {
                "status": "EXECUTION_FAILURE",
                "feedback": f"ToolExecutionError: Tool '{tool_name}' failed with internal error: {str(err)}."
            }
