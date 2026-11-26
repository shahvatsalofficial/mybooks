import asyncio

class AsyncAgentMessage(BaseModel):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    payload: str

class AsyncSwarmBus:
    def __init__(self):
        self.queue: asyncio.Queue[AsyncAgentMessage] = asyncio.Queue()
        self.handlers: Dict[str, Callable[[AsyncAgentMessage], Any]] = {}

    def register_handler(self, agent_name: str, handler: Callable[[AsyncAgentMessage], Any]):
        self.handlers[agent_name] = handler

    async def publish(self, message: AsyncAgentMessage):
        await self.queue.put(message)

    async def run_worker_loop(self, stop_event: asyncio.Event):
        print("[ASYNC BUS] Swarm message dispatch loop online.")
        while not stop_event.is_set():
            try:
                msg = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                handler = self.handlers.get(msg.recipient)
                if handler:
                    await handler(msg)
                else:
                    print(f"[WARN] No handler registered for recipient: {msg.recipient}")
                self.queue.task_done()
            except asyncio.TimeoutError:
                continue
