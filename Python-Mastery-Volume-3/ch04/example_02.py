# Disabling prepared statement caching for PgBouncer compatibility
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "statement_cache_size": 0,       # Completely disables server-side PREPARE
        "prepared_statement_cache_size": 0,
    },
)
