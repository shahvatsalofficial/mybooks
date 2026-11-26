from crewai.memory import LongTermMemory, ShortTermMemory, EntityMemory
from crewai.memory.storage.rag_storage import RAGStorage

# Configure persistent long-term storage
long_term_storage = RAGStorage(
    type="long_term",
    path="./crew_storage/long_term/"
)

crew_with_memory = Crew(
    agents=[cloud_researcher, tech_writer],
    tasks=[research_task],
    process=Process.sequential,
    memory=True, # Master toggle for memory subsystems
    long_term_memory=LongTermMemory(storage=long_term_storage),
    verbose=True
)
