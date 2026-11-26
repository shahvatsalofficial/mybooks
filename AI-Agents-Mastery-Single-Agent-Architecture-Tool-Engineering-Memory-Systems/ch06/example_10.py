class QueryRewriterAgent:
    @staticmethod
    def rewrite_for_retrieval(raw_query: str) -> List[str]:
        # Emulating query expansion and technical keyword synthesis
        base = raw_query.strip().lower()
        expanded = [raw_query]
        
        if "broken" in base or "fix" in base:
            expanded.append(f"troubleshooting error remediation guide {raw_query}")
        if "aws" in base:
            expanded.append("Amazon Web Services IAM CloudWatch ECS architecture")
            
        return expanded

# Verification
expansions = QueryRewriterAgent.rewrite_for_retrieval("Fix broken AWS permission error")
print(f"Generated {len(expansions)} technical query expansions:")
for q in expansions:
    print(f"  -> {q}")
