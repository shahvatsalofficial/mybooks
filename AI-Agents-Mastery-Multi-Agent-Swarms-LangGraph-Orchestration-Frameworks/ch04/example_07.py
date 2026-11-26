from langchain_openai import ChatOpenAI

# 1. Instantiate High-End Reasoning Model for the Manager
manager_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1
)

# 2. Assemble Hierarchical Crew
hierarchical_crew = Crew(
    agents=[cloud_researcher, tech_writer],
    tasks=[research_task, publication_task],
    process=Process.hierarchical,
    manager_llm=manager_llm, # Mandatory for hierarchical process
    verbose=True
)
