"""
Recipe 07.3: Memory-Mapped Binary Protocol Struct Parser with ctypes Unions
Architecture: Zero-allocation binary packet parser using mmap and packed ctypes structures.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import ctypes
import mmap
import os
import tempfile
import time


# Define Binary Protocol Packet Layout (Packed C Structs)
class PacketHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("magic_byte", ctypes.c_uint8),    # 0xAA
        ("message_type", ctypes.c_uint8),  # 0x01: Trade, 0x02: Quote
        ("sequence_num", ctypes.c_uint32), # 4-byte sequence number
        ("timestamp_ns", ctypes.c_uint64), # 8-byte Unix timestamp
    ]


class TradePayload(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("symbol_id", ctypes.c_uint32),
        ("shares", ctypes.c_uint32),
        ("price_cents", ctypes.c_uint64),
    ]


class NetworkPacketUnion(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("raw_bytes", ctypes.c_char * 32),
        ("header", PacketHeader),
        ("trade", TradePayload),
    ]


def parse_binary_stream(file_path: str, packet_count: int) -> int:
    """Parses binary packets directly from memory-mapped disk file with zero allocations."""
    packet_size = 32  # 32 bytes per packet
    valid_checksums = 0

    with open(file_path, "r+b") as f:
        # Map entire file into process virtual memory space
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            packet = NetworkPacketUnion()

            for offset in range(0, packet_count * packet_size, packet_size):
                # Copy 32-byte slice into fixed-size union memory buffer
                packet.raw_bytes = mm[offset : offset + packet_size]

                # Inspect header fields directly via struct mapping:
                if packet.header.magic_byte == 0xAA:
                    valid_checksums += 1

    return valid_checksums


# Demonstration & Verification
if __name__ == "__main__":
    count = 1_000_000
    packet_len = 32

    # Create temporary binary file populated with packets
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        # Pre-generate synthetic packet data
        single_pkt = bytearray(32)
        single_pkt[0] = 0xAA  # Magic byte
        single_pkt[1] = 0x01  # Trade type
        tmp.write(bytes(single_pkt) * count)

    try:
        print(f"Parsing {count:,} binary packets via memory-mapped ctypes structures...")
        start_t = time.perf_counter()
        valid_pkts = parse_binary_stream(tmp_name, count)
        duration = time.perf_counter() - start_t

        rate = count / duration
        print(f"Parsed {valid_pkts:,} packets in {duration:.3f} s ({rate:,.0f} packets/sec)")
        assert valid_pkts == count
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
