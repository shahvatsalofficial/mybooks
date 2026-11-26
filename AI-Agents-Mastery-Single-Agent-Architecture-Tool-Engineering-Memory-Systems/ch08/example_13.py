import random
from typing import Dict, Any

class BlueGreenPromptRouter:
    def __init__(self, canary_weight_green: float = 0.10):
        self.weight_green = canary_weight_green
        self.prompts = {
            "BLUE": "You are a conservative enterprise assistant. Always verify before executing.",
            "GREEN": "You are a high-speed optimized assistant with parallel tool execution."
        }

    def route_request(self) -> Dict[str, str]:
        variant = "GREEN" if random.random() < self.weight_green else "BLUE"
        return {
            "variant": variant,
            "system_prompt": self.prompts[variant]
        }

router = BlueGreenPromptRouter(canary_weight_green=0.20)
samples = [router.route_request()["variant"] for _ in range(100)]
print(f"Blue/Green Traffic Split: Blue={samples.count('BLUE')}%, Green={samples.count('GREEN')}%")
