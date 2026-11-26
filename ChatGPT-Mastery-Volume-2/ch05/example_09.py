"""
Production Adaptive Jitter Buffer for Real-Time Audio
Smooths network arrival variance and prevents buffer underruns.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
import asyncio
from typing import Optional, List
import numpy as np

class AudioPacket:
    def __init__(self, sequence_number: int, timestamp: float, payload: bytes):
        self.sequence_number = sequence_number
        self.timestamp = timestamp
        self.payload = payload

class AdaptiveJitterBuffer:
    def __init__(self, target_delay_ms: float = 40.0, max_buffer_size: int = 50):
        self.target_delay_ms = target_delay_ms
        self.max_buffer_size = max_buffer_size
        self.queue: List[AudioPacket] = []
        self.lock = asyncio.Lock()
        self.last_pop_time = time.perf_counter()

    async def push(self, packet: AudioPacket) -> None:
        async with self.lock:
            # Insert in strict sequence number order
            self.queue.append(packet)
            self.queue.sort(key=lambda p: p.sequence_number)
            
            # Prune obsolete packets if queue overflows
            if len(self.queue) > self.max_buffer_size:
                self.queue.pop(0)

    async def pop_next_frame(self) -> Optional[bytes]:
        async with self.lock:
            if not self.queue:
                return None # Buffer underrun

            # Check if oldest packet has satisfied target buffer latency
            now = time.perf_counter()
            oldest = self.queue[0]
            age_ms = (now - oldest.timestamp) * 1000.0

            if age_ms >= self.target_delay_ms or len(self.queue) > 10:
                pkt = self.queue.pop(0)
                return pkt.payload
            
            return None # Buffering
