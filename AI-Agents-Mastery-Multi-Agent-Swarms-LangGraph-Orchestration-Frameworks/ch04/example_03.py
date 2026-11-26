# Instantiate the Crew with Sequential Process
publishing_crew = Crew(
    agents=[cloud_researcher, tech_writer],
    tasks=[research_task, publication_task],
    process=Process.sequential,
    verbose=True
)
