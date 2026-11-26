# context_compression_engine.py — Enterprise Token Pruning
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class EnterprisePromptCompressor:
    def __init__(self, model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meeting"):
        print(f"Loading small language model for perplexity scoring: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        self.model.eval()

    def compress(
        self,
        prompt: str,
        target_token_budget: int = 2000,
        compression_ratio: float = 0.40
    ) -> Dict[str, Any]:
        """Compresses prompt by pruning low-information tokens."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        input_ids = inputs["input_ids"][0]
        original_length = len(input_ids)

        if original_length <= target_token_budget:
            return {
                "compressed_text": prompt,
                "original_tokens": original_length,
                "compressed_tokens": original_length,
                "savings_pct": 0.0
            }

        # Calculate token perplexities
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
            logits = outputs.logits[0, :-1, :]
            targets = input_ids[1:]
            loss_fn = torch.nn.CrossEntropyLoss(reduction="none")
            token_losses = loss_fn(logits, targets)

        # High loss = high unexpectedness = high information value
        # Preserve structural markers and tokens with highest information density
        retained_count = int(original_length * (1.0 - compression_ratio))
        retained_count = min(retained_count, target_token_budget)
        
        _, top_indices = torch.topk(token_losses, retained_count)
        sorted_indices, _ = torch.sort(top_indices)
        
        compressed_ids = input_ids[sorted_indices]
        compressed_text = self.tokenizer.decode(compressed_ids, skip_special_tokens=True)

        return {
            "compressed_text": compressed_text,
            "original_tokens": original_length,
            "compressed_tokens": len(compressed_ids),
            "savings_pct": round((1.0 - (len(compressed_ids) / original_length)) * 100, 2)
        }
