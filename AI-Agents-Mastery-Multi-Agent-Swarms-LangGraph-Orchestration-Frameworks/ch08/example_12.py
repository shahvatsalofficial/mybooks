class TokenDistributionExporter:
    @staticmethod
    def export(spend_dict: Dict[str, int]) -> str:
        total = sum(spend_dict.values())
        return "\n".join(f"{agent}: {tokens} tokens ({tokens/total*100:.1f}%)" for agent, tokens in spend_dict.items())
