class DualModelCognitiveRouter:
    def __init__(self, system_1_fast_llm: Callable[[str], str], system_2_deliberative_llm: Callable[[str], str]):
        self.fast_model = system_1_fast_llm
        self.slow_model = system_2_deliberative_llm
        # Keywords indicating need for complex deliberation
        self.complexity_triggers = {"refactor", "diagnose", "investigate", "prove", "architect", "split-brain"}

    def route_and_execute(self, prompt: str) -> Tuple[str, str]:
        words = set(re.findall(r"w+", prompt.lower()))
        requires_deep_reasoning = bool(words & self.complexity_triggers) or (len(prompt.split()) > 80)
        
        if requires_deep_reasoning:
            print("[COGNITIVE ROUTER] System 2 Engaged: Dispatching to frontier reasoning model...")
            return "SYSTEM_2_FRONTIER", self.slow_model(prompt)
        else:
            print("[COGNITIVE ROUTER] System 1 Engaged: Fast-path execution...")
            return "SYSTEM_1_FAST", self.fast_model(prompt)

# Verification
def mock_s1(p: str) -> str: return "Fast response: Acknowledged."
def mock_s2(p: str) -> str: return "Deliberative response: Root cause identified across microservices."

router = DualModelCognitiveRouter(mock_s1, mock_s2)
tier, out = router.route_and_execute("Please diagnose split-brain database cluster failure.")
print(f"Tier: {tier} | Response: {out}")
