async def execute_tool_safely(tool_call) -> dict:
    try:
        result = await dispatch_handler(tool_call.function.name, tool_call.function.arguments)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": json.dumps(result)
        }
    except Exception as exc:
        logger.error(f"Tool {tool_call.function.name} failed: {str(exc)}")
        # Re-inject the error message as a valid tool response!
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": json.dumps({
                "status": "ERROR",
                "error_code": "UPSTREAM_SERVICE_TIMEOUT",
                "message": f"Service temporarily unavailable: {str(exc)}"
            })
        }
