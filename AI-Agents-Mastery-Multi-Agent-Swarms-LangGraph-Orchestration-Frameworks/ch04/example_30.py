# Hardened Hierarchical Crew Configuration:
hardened_worker = Agent(
    role="Legal Specialist",
    goal="Extract antitrust citations",
    backstory="Specialist researcher",
    max_iter=3, # Hard stop: worker can only iterate 3 times
    allow_delegation=False # Prevent worker from delegating back to manager
)

hardened_crew = Crew(
    agents=[hardened_worker],
    tasks=[research_task],
    process=Process.hierarchical,
    manager_llm=manager_llm,
    max_iter=5 # Hard stop: manager cannot iterate more than 5 times
)
