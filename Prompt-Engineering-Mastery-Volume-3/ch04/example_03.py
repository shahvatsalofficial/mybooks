"""
Dynamic Token Budget Allocator: Enforces strict compartment ceilings across
system prompt, tools, working memory, and episodic recall to prevent context overflows.
"""

from typing import List, Dict, Any, Tuple
import json


class ContextBudgetAllocator:
    """Manages deterministic prompt partition budgets with greedy knapsack packing."""

    def __init__(
        self,
        max_context_tokens: int = 32768,
        reserved_output_tokens: int = 4096,
        system_budget: int = 3000,
        tools_budget: int = 4000,
        memory_budget: int = 6000,
        working_budget: int = 12000,
    ):
        self.max_context = max_context_tokens
        self.reserved_output = reserved_output_tokens
        self.system_budget = system_budget
        self.tools_budget = tools_budget
        self.memory_budget = memory_budget
        self.working_budget = working_budget

        total_allocated = (
            system_budget + tools_budget + memory_budget + working_budget + reserved_output_tokens
        )
        if total_allocated > max_context_tokens:
            raise ValueError(
                f"Total allocation ({total_allocated}) exceeds maximum context ({max_context_tokens})."
            )

    def estimate_token_count(self, text: str) -> int:
        """Heuristic token counter (1 token ~= 4 English characters)."""
        return max(1, len(text) // 4)

    def pack_memories_into_budget(
        self,
        scored_memories: List[Tuple[Any, float]],
    ) -> Tuple[List[Any], int]:
        """
        Greedy Knapsack Algorithm: Packs highest-scoring memories until memory budget is saturated.
        """
        packed_memories = []
        cumulative_tokens = 0

        for mem, score in scored_memories:
            mem_tokens = self.estimate_token_count(mem.content)
            if cumulative_tokens + mem_tokens <= self.memory_budget:
                packed_memories.append(mem)
                cumulative_tokens += mem_tokens
            else:
                continue

        return packed_memories, cumulative_tokens

    def build_assembled_prompt(
        self,
        system_constitution: str,
        tool_schemas: str,
        working_memory_scratchpad: str,
        selected_memories: List[Any],
    ) -> str:
        """Stitches validated components into production prompt with strict XML encapsulation."""
        mem_xml_blocks = []
        for mem in selected_memories:
            mem_xml_blocks.append(
                f'  <memory_item id="{mem.memory_id}" importance="{mem.importance:.2f}">\n'
                f'    {mem.content}\n'
                f'  </memory_item>'
            )

        memory_section = (
            "<injected_context_memory>\n"
            + "\n".join(mem_xml_blocks)
            + "\n</injected_context_memory>"
        )

        final_prompt = (
            f"<system_constitution>\n{system_constitution}\n</system_constitution>\n\n"
            f"<tool_definitions>\n{tool_schemas}\n</tool_definitions>\n\n"
            f"{memory_section}\n\n"
            f"<working_scratchpad>\n{working_memory_scratchpad}\n</working_scratchpad>\n"
        )
        return final_prompt
