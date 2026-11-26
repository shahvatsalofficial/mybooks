"""
Comparative Tokenization Benchmark: cl100k_base vs o200k_base
Demonstrates the algorithmic compression superiority of modern tokenizers.
"""
import tiktoken

def benchmark_tokenizers():
    test_corpora = {
        "Python Code": """
        async def fetch_financial_metrics(ticker: str, start_date: str) -> dict[str, float]:
            query = f"SELECT revenue, net_income FROM financial_reports WHERE symbol = '{ticker}'"
            return await db_pool.execute_query(query)
        """,
        "Multilingual Prose (Gujarati)": "કૃત્રિમ બુદ્ધિમત્તા આધુનિક એન્ટરપ્રાઇઝ સોફ્ટવેર આર્કિટેક્ચરનું ભવિષ્ય બદલી રહી છે.",
        "JSON Enterprise Payload": """
        {"transaction_id": "tx_99812489", "status": "COMPLETED", "amount_cents": 450000, "currency": "USD"}
        """
    }
    
    enc_cl100k = tiktoken.get_encoding("cl100k_base")
    enc_o200k = tiktoken.get_encoding("o200k_base")
    
    print(f"{'Category':<30} | {'cl100k Count':<12} | {'o200k Count':<12} | {'Efficiency Gain':<15}")
    print("-" * 75)
    
    for category, text in test_corpora.items():
        tokens_cl = len(enc_cl100k.encode(text))
        tokens_o2 = len(enc_o200k.encode(text))
        gain = ((tokens_cl - tokens_o2) / tokens_cl) * 100
        print(f"{category:<30} | {tokens_cl:<12} | {tokens_o2:<12} | {gain:>13.2f}%")

if __name__ == "__main__":
    benchmark_tokenizers()
