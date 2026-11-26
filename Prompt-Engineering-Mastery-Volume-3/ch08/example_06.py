"""
Moore Tool-Masking Middleware: Filters available tools presented to the LLM
strictly based on current state, physically preventing out-of-order execution.
"""

from typing import List, Dict, Any


class MooreToolMaskingMiddleware:
    """Restricts API schema visibility strictly to authorized state tools."""

    def __init__(self, master_tool_catalog: List[Dict[str, Any]]):
        self.catalog = {tool["function"]["name"]: tool for tool in master_tool_catalog}

    def filter_tool_definitions(self, allowed_tool_names: List[str]) -> List[Dict[str, Any]]:
        """
        Returns only the tool schemas explicitly whitelisted for the active state.
        Tools belonging to other states are completely purged from the context.
        """
        filtered_tools = []
        for name in allowed_tool_names:
            if name in self.catalog:
                filtered_tools.append(self.catalog[name])
            else:
                raise KeyError(f"Tool '{name}' declared in state not found in master catalog.")

        return filtered_tools
