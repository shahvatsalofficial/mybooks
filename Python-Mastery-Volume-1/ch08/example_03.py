class DatabaseUnavailableError(Exception):
    """Raised when the primary relational cluster is unreachable."""

def execute_query(sql: str) -> dict:
    try:
        return raw_socket_query(sql)
    except ConnectionRefusedError as original_error:
        # Explicit Chaining: Sets __cause__
        raise DatabaseUnavailableError("Failed to reach Postgres Primary on 5432") from original_error
