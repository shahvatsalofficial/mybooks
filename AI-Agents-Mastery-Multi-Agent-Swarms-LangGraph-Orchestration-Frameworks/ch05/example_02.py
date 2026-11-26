# 1. Define Coder Assistant Agent
coder_agent = AssistantAgent(
    name="SeniorSoftwareEngineer",
    system_message=(
        "You are an expert Python software engineer. You write complete, self-contained, "
        "production-grade Python code blocks. When given an objective, provide the full executable "
        "code enclosed in ```python markdown blocks. Once the UserProxy confirms that the code "
        "executed successfully and emitted the required output, reply with exactly 'TERMINATE'."
    ),
    llm_config=llm_config
)

# 2. Define UserProxyAgent with Execution Capabilities
user_proxy = UserProxyAgent(
    name="ExecutionEnvironmentProxy",
    system_message="A human admin and local code execution gateway.",
    code_execution_config={
        "work_dir": "workspace_autogen_run", # Isolated directory on disk
        "use_docker": False # Set to True in production Docker deployments
    },
    human_input_mode="NEVER", # Fully autonomous execution
    max_consecutive_auto_reply=5, # Hard turn ceiling to prevent infinite loops
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", "").strip()
)
