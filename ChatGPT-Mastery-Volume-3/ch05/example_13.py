# prompt_compressor.py
from llmlingua import PromptCompressor

class EnterprisePromptCompressor:
    def __init__(self, model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meeting"):
        self.compressor = PromptCompressor(
            model_name=model_name,
            use_fp16=True
        )

    def compress_context(self, long_prompt: str, target_ratio: float = 0.5) -> dict:
        """
        Compresses long prompt contexts by up to 50% while preserving key facts and reasoning.
        """
        results = self.compressor.compress_prompt(
            long_prompt.split("\n\n"),
            rate=target_ratio,
            condition_in_question="after_condition",
            reorder_context="sort"
        )
        
        return {
            "compressed_prompt": results["compressed_prompt"],
            "original_tokens": results["origin_tokens"],
            "compressed_tokens": results["compressed_tokens"],
            "saving_ratio": (1 - results["compressed_tokens"] / results["origin_tokens"]) * 100
        }
