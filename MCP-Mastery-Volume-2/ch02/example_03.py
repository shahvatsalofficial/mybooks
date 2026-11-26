import contextvars

async def safe_tenant_stream(async_gen_func, *args, **kwargs):
    """Guarantees generator ticks execute strictly within the captured tenant context."""
    ctx = contextvars.copy_context()
    gen = async_gen_func(*args, **kwargs)
    try:
        while True:
            # Step the generator inside the isolated context
            item = await ctx.run(gen.__anext__)
            yield item
    except StopAsyncIteration:
        pass
    finally:
        await ctx.run(gen.aclose)
