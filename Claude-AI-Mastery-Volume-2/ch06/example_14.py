# Production Patch: Supervised Background Execution with AnyIO TaskGroup
from anyio import create_task_group

class TaskSupervisor:
    def __init__(self):
        self._tg = None

    async def initialize(self):
        self._tg = create_task_group()
        await self._tg.__aenter__()

    async def shutdown(self):
        if self._tg:
            await self._tg.__aexit__(None, None, None)

    def spawn(self, coro, *args):
        self._tg.start_soon(coro, *args)

# Safe completion callback alternative for native asyncio:
def safe_task_callback(task: asyncio.Task):
    try:
        task.result()
    except Exception as exc:
        logger.error(f"Background telemetry task failed safely without terminating process: {exc}")

@mcp.tool()
async def track_container_status(container_id: str) -> str:
    task = asyncio.create_task(emit_telemetry_webhook(container_id))
    task.add_done_callback(safe_task_callback)
    return "Status recorded."
