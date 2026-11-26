class SubQuestion(BaseModel):
    sub_query: str
    target_tool: str

class SubQuestionEngine:
    def __init__(self, tools: Dict[str, QueryEngineTool]):
        self.tools = tools

    def decompose(self, master_prompt: str) -> List[SubQuestion]:
        # Rule-based decomposition for verification
        return [
            SubQuestion(sub_query="What was Acme gross margin in 2025?", target_tool="query_sec_filings"),
            SubQuestion(sub_query="What was Acme cloud spend in 2025?", target_tool="query_sec_filings"),
            SubQuestion(sub_query="How many Kubernetes clusters are deployed?", target_tool="query_engineering_docs")
        ]

    def execute_sub_questions(self, master_prompt: str) -> Dict[str, Any]:
        sub_questions = self.decompose(master_prompt)
        collected_evidence = []
        
        for sq in sub_questions:
            tool = self.tools.get(sq.target_tool)
            if tool:
                res = tool.execute(sq.sub_query)
                collected_evidence.append({
                    "sub_query": sq.sub_query,
                    "evidence": res
                })
        
        return {
            "master_prompt": master_prompt,
            "evidence_count": len(collected_evidence),
            "evidence": collected_evidence
        }

# Verification
sub_engine = SubQuestionEngine(tools={"query_sec_filings": tool_sec, "query_engineering_docs": tool_eng})
report = sub_engine.execute_sub_questions("Perform deep-dive analysis into Acme 2025 operations.")
print("Sub-Question Execution Report:")
print(json.dumps(report, indent=2))
