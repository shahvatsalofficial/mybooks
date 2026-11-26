import asyncio
import json
import redis.asyncio as aioredis
from typing import List, Dict, Any

class RedisShortTermMemory:
    """
    Production-grade Redis Short-Term Memory Manager
    Features token-aware sliding window, TTL session expiration, and message buffering.
    """
    def __init__(self, redis_url: str, session_id: str, max_tokens: int = 4096, ttl_seconds: int = 86400):
        self.redis_url = redis_url
        self.session_id = f"session:{session_id}:messages"
        self.max_tokens = max_tokens
        self.ttl = ttl_seconds
        self.client = None

    async def connect(self):
        if not self.client:
            self.client = aioredis.from_url(self.redis_url, decode_responses=True)

    async def append_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        await self.connect()
        message_payload = json.dumps({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": asyncio.get_event_loop().time()
        })
        
        async with self.client.pipeline(transaction=True) as pipe:
            pipe.rpush(self.session_id, message_payload)
            pipe.expire(self.session_id, self.ttl)
            await pipe.execute()

    async def get_active_context(self) -> List[Dict[str, Any]]:
        await self.connect()
        raw_messages = await self.client.lrange(self.session_id, 0, -1)
        parsed_messages = [json.loads(m) for m in raw_messages]
        
        # Token estimation (4 chars ~= 1 token)
        total_tokens = sum(len(m["content"]) // 4 for m in parsed_messages)
        
        if total_tokens > self.max_tokens:
            return self._trim_messages(parsed_messages)
        return parsed_messages

    def _trim_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep system message + most recent turns within max token budget."""
        trimmed = []
        current_tokens = 0
        
        # Always preserve system message if present
        system_msg = next((m for m in messages if m["role"] == "system"), None)
        if system_msg:
            trimmed.append(system_msg)
            current_tokens += len(system_msg["content"]) // 4

        # Iterate backwards through recent messages
        recent_buffer = []
        for m in reversed(messages):
            if m["role"] == "system":
                continue
            msg_tokens = len(m["content"]) // 4
            if current_tokens + msg_tokens > self.max_tokens:
                break
            recent_buffer.append(m)
            current_tokens += msg_tokens

        trimmed.extend(reversed(recent_buffer))
        return trimmed

    async def close(self):
        if self.client:
            await self.client.close()
