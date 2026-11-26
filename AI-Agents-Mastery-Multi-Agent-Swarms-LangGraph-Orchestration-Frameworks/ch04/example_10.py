governed_crew = Crew(
    agents=[cloud_researcher, tech_writer],
    tasks=[research_task],
    process=Process.sequential,
    max_rpm=30, # Hard ceiling: 30 requests per minute across entire crew
    verbose=True
)
