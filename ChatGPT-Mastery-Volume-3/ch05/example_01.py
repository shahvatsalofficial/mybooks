def route_query_to_optimal_model(query: str, history: List[dict]) -> str:
    # 1. Rule-based Fast Path: Direct keywords
    if contains_math_or_code_synthesis(query):
        return "o1-preview"
    
    # 2. Token Volume Evaluation
    token_len = estimate_tokens(query)
    if token_len < 150 and is_standard_faq(query):
        return "gpt-4o-mini"
    
    # 3. Semantic Classifier Path
    complexity_score = evaluate_prompt_complexity(query)
    if complexity_score < 0.35:
        return "gpt-4o-mini"
    elif complexity_score < 0.85:
        return "gpt-4o"
    else:
        return "o1-mini"
