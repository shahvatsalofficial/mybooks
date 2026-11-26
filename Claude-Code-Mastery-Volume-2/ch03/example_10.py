@mcp.tool()
async def classify_unstructured_error(raw_stack_trace: str, ctx: Context) -> str:
    """Classifies an obscure enterprise error log using the host model's reasoning engine."""
    ctx.info("Requesting reverse sampling from Claude Code host...")
    
    prompt = f"Analyze this enterprise stack trace and identify the failing subsystem in 1 sentence:
{raw_stack_trace}"
    
    # Tool queries the host model directly!
    sample_response = await ctx.sample(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    
    classified_subsystem = sample_response.text.strip()
    ctx.info(f"Host classified root subsystem as: {classified_subsystem}")
    return f"Classification: {classified_subsystem}"
