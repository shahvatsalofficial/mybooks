"""
prompt_compression_engine.py
Enterprise Prompt Compression Engine using LLMLingua
Reduces input token consumption by 50-75% before submitting to Azure OpenAI.
"""

from typing import Dict, Any
# from llmlingua import PromptCompressor


class EnterprisePromptCompressor:
    def __init__(self, model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meeting"):
        print(f"[*] Initializing LLMLingua Compressor with base model: {model_name}")
        # In production: self.compressor = PromptCompressor(model_name=model_name, device_map="cuda")

    def compress_context(
        self,
        original_prompt: str,
        target_rate: float = 0.40,
        preserve_keywords: list = None
    ) -> Dict[str, Any]:
        """
        Compresses input prompt by dynamically evaluating token perplexity.
        Target rate = 0.40 means retain 40% of tokens (60% compression).
        """
        # Simulated compression for demonstration:
        words = original_prompt.split()
        original_token_count = len(words) * 1.3
        
        # In production:
        # result = self.compressor.compress_prompt(
        #     original_prompt,
        #     rate=target_rate,
        #     force_words=preserve_keywords or [],
        #     use_sentence_level_filter=True
        # )
        
        compressed_text = " ".join([w for i, w in enumerate(words) if i % 2 == 0 or w[0].isupper()])
        compressed_token_count = len(compressed_text.split()) * 1.3
        
        savings_percent = ((original_token_count - compressed_token_count) / original_token_count) * 100
        
        return {
            "compressed_prompt": compressed_text,
            "original_tokens": int(original_token_count),
            "compressed_tokens": int(compressed_token_count),
            "savings_percent": round(savings_percent, 2)
        }


if __name__ == "__main__":
    compressor = EnterprisePromptCompressor()
    sample_legal_clause = (
        "The receiving party agrees that it shall maintain the confidential information in strict "
        "confidence and shall not disclose any proprietary aspects of the technology to any third party "
        "without the prior express written authorization of the disclosing party, subject to statutory exemptions."
    )
    res = compressor.compress_context(sample_legal_clause, target_rate=0.40)
    print(f"Original Tokens: {res['original_tokens']}")
    print(f"Compressed Tokens: {res['compressed_tokens']}")
    print(f"Token Savings: {res['savings_percent']}%")
    print(f"Compressed Text:
{res['compressed_prompt']}")
