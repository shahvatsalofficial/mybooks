cmd_builder = StateGraph(TriagedState)
cmd_builder.add_node("tier1_support", tier1_support_node)
cmd_builder.add_node("tier2_specialist", tier2_specialist_node)

cmd_builder.add_edge(START, "tier1_support")
# Notice: No conditional edges required! Routing is handled dynamically by Command.

cmd_app = cmd_builder.compile()
