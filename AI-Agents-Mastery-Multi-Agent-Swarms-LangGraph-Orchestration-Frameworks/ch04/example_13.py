class EnterpriseCrewPipeline:
    def __init__(self, research_crew: Crew, publication_crew: Crew):
        self.research_crew = research_crew
        self.publication_crew = publication_crew

    def run_pipeline(self, initial_query: str) -> str:
        print("[PIPELINE] Phase 1: Executing Research Crew...")
        research_output = self.research_crew.kickoff(inputs={"query": initial_query})
        
        print("[PIPELINE] Phase 2: Passing findings into Publication Crew...")
        final_doc = self.publication_crew.kickoff(inputs={"research_context": str(research_output)})
        
        return str(final_doc)
