class SQLVectorHybridSynthesizer:
    def __init__(self, sql_fn: Callable[[str], Dict[str, Any]], vector_fn: Callable[[str], str]):
        self.sql_fn = sql_fn
        self.vector_fn = vector_fn

    def answer_composite_query(self, sql_query: str, vector_query: str) -> str:
        # Step 1: Execute relational aggregation
        sql_data = self.sql_fn(sql_query)
        # Step 2: Execute semantic vector search
        vector_text = self.vector_fn(vector_query)
        # Step 3: Synthesize
        return f"Structured Fact: {json.dumps(sql_data)} | Unstructured Context: {vector_text}"

# Verification
def mock_sql(q: str):
    return {"max_refund_order": "ORD-9912", "amount": "$450.00", "customer": "CUST-104"}

def mock_vector(q: str):
    return "Customer reported shipping box arrived torn and contents broken."

hybrid_syn = SQLVectorHybridSynthesizer(mock_sql, mock_vector)
print(hybrid_syn.answer_composite_query("SELECT max(amount) ...", "shipping damage complaint"))
