human_reviewed_task = Task(
    description="Draft deployment plan for Kubernetes cluster upgrade.",
    expected_output="Step-by-step upgrade plan with rollback triggers.",
    agent=cloud_researcher,
    human_input=True # Halts execution and awaits human terminal review
)
