"""
OpenAI Vision Tile Budget & Token Economics Calculator
Author: Vatsal Shah, Enterprise AI Architect
Version: 2.0 (High-Precision Math)
"""
import math
from typing import Tuple, Dict

class VisionEconomicsCalculator:
    PRICE_PER_MILLION_INPUT_TOKENS = 2.50 # gpt-4o pricing

    @classmethod
    def calculate_image_cost(cls, width: int, height: int, detail: str = "high") -> Dict[str, any]:
        if detail == "low":
            tokens = 85
            cost = (tokens / 1_000_000) * cls.PRICE_PER_MILLION_INPUT_TOKENS
            return {
                "detail": "low",
                "original_res": f"{width}x{height}",
                "tiles": 0,
                "tokens": tokens,
                "estimated_cost_usd": round(cost, 6)
            }

        # Step 1: Max Bounding Box Constraining (2048x2048)
        scale_max = min(1.0, 2048.0 / max(width, height))
        w1 = width * scale_max
        h1 = height * scale_max

        # Step 2: Scale shortest side to 768px
        scale_short = 768.0 / min(w1, h1)
        w_final = w1 * scale_short
        h_final = h1 * scale_short

        # Step 3: Compute 512x512 tile counts
        cols = math.ceil(w_final / 512.0)
        rows = math.ceil(h_final / 512.0)
        total_tiles = cols * rows

        # Step 4: Compute token formula: (Tiles * 170) + 85
        tokens = (total_tiles * 170) + 85
        cost = (tokens / 1_000_000) * cls.PRICE_PER_MILLION_INPUT_TOKENS

        return {
            "detail": "high",
            "original_res": f"{width}x{height}",
            "scaled_res": f"{round(w_final)}x{round(h_final)}",
            "grid": f"{cols}x{rows}",
            "total_tiles": total_tiles,
            "tokens": tokens,
            "estimated_cost_usd": round(cost, 6)
        }

if __name__ == "__main__":
    calc = VisionEconomicsCalculator()
    print("--- Vision Cost Audits ---")
    print(calc.calculate_image_cost(1920, 1080))
    print(calc.calculate_image_cost(3840, 2160))
    print(calc.calculate_image_cost(4096, 512))
