"""
Recipe 05.3: SPSC Shared Memory Ring Buffer
File: recipe_05_3_spsc_ring_buffer.py
Python Version: 3.12+
"""

from __future__ import annotations
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
import struct
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [PID %(process)d] %(message)s")
logger = logging.getLogger("SPSCRingBuffer")

# Ring Header Specification (16 bytes):
# [0:8]  Head Index (uint64) - Written by Producer
# [8:16] Tail Index (uint64) - Written by Consumer
HEADER_STRUCT = struct.Struct("!QQ")
HEADER_SIZE = HEADER_STRUCT.size # 16 bytes

# Slot Specification (32 bytes per message):
# [0:8]   Timestamp (uint64)
# [8:12]  Message ID (uint32)
# [12:20] Price (double)
# [20:32] Reserved Padding (12 bytes)
SLOT_STRUCT = struct.Struct("!QId12s")
SLOT_SIZE = SLOT_STRUCT.size # 32 bytes

BUFFER_CAPACITY = 1024 # Must be power of 2
TOTAL_SHM_SIZE = HEADER_SIZE + (BUFFER_CAPACITY * SLOT_SIZE)


class SharedRingBuffer:
    def __init__(self, shm_buffer: memoryview) -> None:
        self.buf = shm_buffer
        self.capacity = BUFFER_CAPACITY
        self.mask = BUFFER_CAPACITY - 1

    def write_message(self, msg_id: int, price: float) -> bool:
        """Pushes a message if ring is not full. Non-blocking lock-free write."""
        head, tail = HEADER_STRUCT.unpack_from(self.buf, 0)
        
        # Check if full: head cannot advance beyond tail + capacity
        if (head - tail) >= self.capacity:
            return False # Queue full, backpressure!

        slot_offset = HEADER_SIZE + ((head & self.mask) * SLOT_SIZE)
        timestamp_ns = time.time_ns()
        SLOT_STRUCT.pack_into(self.buf, slot_offset, timestamp_ns, msg_id, price, b"\x00" * 12)
        
        # Atomic release: Advance head pointer
        HEADER_STRUCT.pack_into(self.buf, 0, head + 1, tail)
        return True

    def read_message(self) -> tuple[int, int, float] | None:
        """Reads a message if ring is not empty. Non-blocking lock-free read."""
        head, tail = HEADER_STRUCT.unpack_from(self.buf, 0)
        
        # Check if empty: tail caught up to head
        if tail >= head:
            return None # Queue empty

        slot_offset = HEADER_SIZE + ((tail & self.mask) * SLOT_SIZE)
        timestamp_ns, msg_id, price, _ = SLOT_STRUCT.unpack_from(self.buf, slot_offset)
        
        # Atomic release: Advance tail pointer
        HEADER_STRUCT.pack_into(self.buf, 0, head, tail + 1)
        return timestamp_ns, msg_id, price


def producer_worker(shm_name: str, count: int) -> None:
    shm = SharedMemory(name=shm_name)
    ring = SharedRingBuffer(shm.buf)
    logger.info(f"Producer transmitting {count} messages...")
    
    for i in range(1, count + 1):
        price = 100.0 + (i * 0.05)
        while not ring.write_message(i, price):
            time.sleep(0.0001) # Yield CPU on full queue
            
    logger.info("Producer completed all transmissions.")
    shm.close()


def consumer_worker(shm_name: str, count: int) -> None:
    shm = SharedMemory(name=shm_name)
    ring = SharedRingBuffer(shm.buf)
    logger.info("Consumer listening for messages...")
    
    received = 0
    start_time = time.perf_counter()
    
    while received < count:
        msg = ring.read_message()
        if msg is not None:
            received += 1
        else:
            time.sleep(0.0001) # Yield CPU on empty queue

    elapsed = time.perf_counter() - start_time
    rate = received / elapsed
    logger.info(f"Consumer drained {received} messages in {elapsed*1000:.2f}ms ({rate:.0f} msg/sec).")
    shm.close()


def run_spsc_demonstration() -> None:
    shm = SharedMemory(create=True, size=TOTAL_SHM_SIZE)
    # Zero out header
    HEADER_STRUCT.pack_into(shm.buf, 0, 0, 0)

    NUM_MESSAGES = 100_000
    try:
        p_cons = mp.Process(target=consumer_worker, args=(shm.name, NUM_MESSAGES))
        p_prod = mp.Process(target=producer_worker, args=(shm.name, NUM_MESSAGES))
        
        p_cons.start()
        p_prod.start()
        
        p_prod.join()
        p_cons.join()
    finally:
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    run_spsc_demonstration()
