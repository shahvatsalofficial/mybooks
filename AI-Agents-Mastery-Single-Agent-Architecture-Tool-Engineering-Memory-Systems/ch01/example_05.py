class MockLLMStepper:
    """Simulates an LLM responding with multi-turn ReAct tokens."""
    def __init__(self):
        self.step = 0

    def complete(self, prompt: str) -> str:
        self.step += 1
        if self.step == 1:
            return """Thought: I need to query the database to locate order ORD-9912.
Action: query_database({"table": "orders", "filter_key": "order_id", "filter_value": "ORD-9912"})"""
        elif self.step == 2:
            return """Thought: The order was delivered but the customer requested a refund. I will issue a refund for 4500 cents.
Action: issue_refund({"order_id": "ORD-9912", "amount_cents": 4500, "reason": "Customer satisfaction guarantee"})"""
        else:
            return """Thought: The refund transaction has been confirmed by the billing ledger.
Final Answer: Refund TX-REF-ORD-9912 processed successfully for amount $45.00."""

class EnterpriseAgentRunner:
    def __init__(self, llm: MockLLMStepper, registry: ProductionToolRegistry, governor: ContextGovernor):
        self.llm = llm
        self.registry = registry
        self.governor = governor

    def run(self, user_goal: str, max_turns: int = 5) -> str:
        self.governor.add_message(Role.USER, user_goal)
        
        for turn in range(1, max_turns + 1):
            prompt_context = self.governor.export_context()
            serialized_prompt = "
".join(f"{m['role']}: {m['content']}" for m in prompt_context)
            
            raw_response = self.llm.complete(serialized_prompt)
            thought, tool_name, args_str = parse_agent_output(raw_response)
            
            self.governor.add_message(Role.ASSISTANT, raw_response)
            
            if tool_name is None:
                # Terminal condition reached
                return raw_response
            
            # Execute tool action
            try:
                args_dict = json.loads(args_str) if args_str else {}
                obs = self.registry.invoke(tool_name, args_dict)
                self.governor.add_message(Role.TOOL, f"Observation: {obs}")
            except Exception as e:
                self.governor.add_message(Role.TOOL, f"Observation Error: {str(e)}")
                
        return "ERROR: Maximum turn budget exhausted without terminal convergence."

# Verification of Recipe 1.5
mock_llm = MockLLMStepper()
runner = EnterpriseAgentRunner(llm=mock_llm, registry=registry, governor=governor)
final_result = runner.run("Please resolve refund for order ORD-9912.")
print("Runner Execution Complete:")
print(final_result)
