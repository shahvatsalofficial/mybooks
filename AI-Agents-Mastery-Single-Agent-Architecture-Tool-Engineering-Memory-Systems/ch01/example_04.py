from string import Template

class AgentPromptEngine:
    SYSTEM_TEMPLATE = """You are $agent_name (Version $version).
Primary Directive: $objective

Operational Constraints:
1. You must validate all tool inputs against schema boundaries.
2. If a tool returns an error, hypothesize the cause and formulate an alternative approach.
3. Never invent facts or assume successful execution without verifying observations.

Available Capabilities:
$tools_manifest
"""

    SCRATCHPAD_HEADER = """--- CURRENT WORKING TRAJECTORY ---
Task ID: $task_id
Turn Count: $turn_count / $max_turns
Remaining Budget: $remaining_budget USD
"""

    def __init__(self, agent_name: str, version: str, objective: str, tools: List[str]):
        self.agent_name = agent_name
        self.version = version
        self.objective = objective
        self.tools = tools

    def render_system_prompt(self) -> str:
        manifest = "
".join(f"- {t}" for t in self.tools)
        return Template(self.SYSTEM_TEMPLATE).substitute(
            agent_name=self.agent_name,
            version=self.version,
            objective=self.objective,
            tools_manifest=manifest
        )

    def render_scratchpad(self, task_id: str, turn: int, max_turns: int, budget: float) -> str:
        return Template(self.SCRATCHPAD_HEADER).substitute(
            task_id=task_id,
            turn_count=turn,
            max_turns=max_turns,
            remaining_budget=f"{budget:.4f}"
        )

# Verification
engine = AgentPromptEngine(
    agent_name="SovereignSentinel",
    version="2.4.0",
    objective="Autonomous vulnerability triage across internal git repositories",
    tools=["git_blame_analyzer", "cve_lookup_gateway", "patch_synthesizer"]
)
print(engine.render_system_prompt()[:300] + "...")
