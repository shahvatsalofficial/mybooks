import anyio

# Configure enterprise thread pool capacity for blocking data engineering tools
limiter = anyio.to_thread.current_default_thread_limiter()
limiter.total_tokens = 120 # Allow up to 120 concurrent synchronous worker threads
