class ResilientGatewayClient:
    def __init__(self, exit_stack: AsyncExitStack, http_session, cache_conn) -> None:
        self._stack = exit_stack
        self.http_session = http_session
        self.cache_conn = cache_conn

    @classmethod
    async def create(cls, endpoint: str) -> Self:
        async with AsyncExitStack() as setup_stack:
            # Step 1: Acquire TLS certificate context
            ssl_ctx = await setup_stack.enter_async_context(acquire_ssl_context())
            
            # Step 2: Open HTTP/2 persistent session
            http_session = await setup_stack.enter_async_context(httpx.AsyncClient(verify=ssl_ctx))
            
            # Step 3: Connect to Redis local caching layer
            cache_conn = await setup_stack.enter_async_context(redis_pool.connection())
            
            # Step 4: Verify health check probe (might raise ConnectionError!)
            probe_resp = await http_session.get(f"{endpoint}/healthz")
            probe_resp.raise_for_status()
            
            # SUCCESS: All components verified healthy!
            # Transfer ownership of all teardown callbacks away from the setup_stack!
            active_stack = setup_stack.pop_all()
            return cls(active_stack, http_session, cache_conn)
            
        # If any line in Step 1-4 raises an error, setup_stack DOES NOT reach pop_all().
        # When exiting the block, setup_stack unwinds in reverse LIFO order,
        # closing the cache_conn, shutting down http_session, and releasing ssl_ctx!
        # ZERO LEAKS GUARANTEED.

    async def close(self) -> None:
        """Explicitly shut down client and unwind all underlying resources."""
        await self._stack.aclose()
