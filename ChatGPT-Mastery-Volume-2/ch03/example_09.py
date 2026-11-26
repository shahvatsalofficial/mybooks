"""
Distributed Thread Mutex for OpenAI Assistants API v2
Prevents 'active_run_exists' race conditions across distributed microservice pods.
"""
import asyncio
import time
import uuid
import logging
from typing import Optional
import redis.asyncio as aioredis
from openai import AsyncOpenAI, BadRequestError

logger = logging.getLogger("ThreadLock")

class DistributedThreadLock:
    def __init__(self, redis_client: aioredis.Redis, thread_id: str, ttl_seconds: int = 120):
        self.redis = redis_client
        self.thread_id = thread_id
        self.lock_key = f"lock:thread:{thread_id}"
        self.lock_value = str(uuid.uuid4())
        self.ttl = ttl_seconds

    async def acquire(self, timeout_seconds: float = 15.0) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Atomic set-if-not-exists with expiration (NX PX)
            acquired = await self.redis.set(
                self.lock_key, 
                self.lock_value, 
                nx=True, 
                ex=self.ttl
            )
            if acquired:
                logger.info(f"Acquired distributed lock on thread {self.thread_id}")
                return True
            await asyncio.sleep(0.2)
        return False

    async def release(self) -> None:
        # Atomic release using Lua script to guarantee we only delete our own lock
        lua_release = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        await self.redis.eval(lua_release, 1, self.lock_key, self.lock_value)
        logger.info(f"Released lock on thread {self.thread_id}")

class ResilientThreadRunner:
    def __init__(self, openai_client: AsyncOpenAI, redis_client: aioredis.Redis):
        self.client = openai_client
        self.redis = redis_client

    async def run_safe_turn(self, thread_id: str, assistant_id: str, prompt: str):
        lock = DistributedThreadLock(self.redis, thread_id)
        if not await lock.acquire(timeout_seconds=20.0):
            raise TimeoutError(f"Contention timeout: Thread {thread_id} is locked by another active process.")

        try:
            # 1. Double-check for zombie runs
            runs = await self.client.beta.threads.runs.list(thread_id=thread_id, limit=3)
            for r in runs.data:
                if r.status in ["queued", "in_progress", "requires_action"]:
                    logger.warning(f"Found active run {r.id}. Cancelling to clear thread...")
                    await self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=r.id)
                    # Await cancellation
                    for _ in range(20):
                        chk = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=r.id)
                        if chk.status in ["cancelled", "failed", "completed", "expired"]:
                            break
                        await asyncio.sleep(0.5)

            # 2. Add message and execute run
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )

            run = await self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
                max_prompt_tokens=8000
            )
            return run

        finally:
            await lock.release()
