def safe_tool_wrapper(func: Callable, max_chars: int = 4000) -> Callable:
    def wrapper(*args, **kwargs) -> str:
        raw_result = func(*args, **kwargs)
        result_str = str(raw_result)
        if len(result_str) > max_chars:
            truncated = result_str[:max_chars]
            return f"{truncated}\n... [TRUNCATED: Output exceeded {max_chars} chars. Use pagination parameters to fetch more.]"
        return result_str
    return wrapper
