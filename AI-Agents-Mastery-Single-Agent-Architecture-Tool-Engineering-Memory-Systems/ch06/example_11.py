class IndexRouterCoordinator:
    def __init__(self, indexes: Dict[str, str]):
        self.index_descriptions = indexes

    def route_query(self, user_prompt: str) -> List[str]:
        # Classify intent against registered index metadata
        prompt_lower = user_prompt.lower()
        selected = []
        if any(term in prompt_lower for term in ["contract", "liability", "terms", "nda"]):
            selected.append("legal_index")
        if any(term in prompt_lower for term in ["vacation", "pto", "benefits", "401k"]):
            selected.append("hr_index")
        if any(term in prompt_lower for term in ["api", "deploy", "server", "code", "database"]):
            selected.append("engineering_index")
            
        return selected if selected else ["engineering_index"] # Default fallback

# Verification
router_coord = IndexRouterCoordinator({
    "legal_index": "Corporate contracts and nondisclosure agreements",
    "hr_index": "Employee handbook, PTO policies, and health benefits",
    "engineering_index": "API documentation and cloud system architecture"
})
print("Routed Query 1:", router_coord.route_query("What is our policy on parental leave?"))
print("Routed Query 2:", router_coord.route_query("How do I rotate database credentials?"))
