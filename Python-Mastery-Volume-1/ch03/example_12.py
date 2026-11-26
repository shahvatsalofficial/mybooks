"""
Recipe 03.1: Zero-Copy Network Packet Parsing Engine
File: recipe_03_1_zero_copy_parser.py
Python Version: 3.12+
"""

from __future__ import annotations
import struct
from typing import NamedTuple, Generator, Tuple

# Binary Wire Specification:
# [0:4]   Magic Number (0xDEADBEEF) -> 32-bit uint
# [4:8]   Sequence ID               -> 32-bit uint
# [8:10]  Opcode                    -> 16-bit uint
# [10:14] Payload Length (N)        -> 32-bit uint
# [14:16] Checksum                  -> 16-bit uint
# [16:16+N] Payload Bytes
HEADER_FORMAT = "!IIHIH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # Exactly 16 bytes
MAGIC_CONSTANT = 0xDEADBEEF

HEADER_STRUCT = struct.Struct(HEADER_FORMAT)


class PacketHeader(NamedTuple):
    magic: int
    seq_id: int
    opcode: int
    payload_len: int
    checksum: int


class ZeroCopyNetworkParser:
    """High-throughput packet parser operating on zero-copy memoryview windows."""

    def __init__(self, initial_buffer_size: int = 65536) -> None:
        self._buffer = bytearray(initial_buffer_size)
        self._view = memoryview(self._buffer)
        self._bytes_in_buffer = 0

    def get_write_buffer(self) -> memoryview:
        """Returns a zero-copy memoryview slice for direct socket.recv_into() ingestion."""
        return self._view[self._bytes_in_buffer :]

    def advance_write_pointer(self, bytes_received: int) -> None:
        """Updates internal write boundary following a successful network read."""
        self._bytes_in_buffer += bytes_received

    def parse_packets(self) -> Generator[Tuple[PacketHeader, memoryview], None, None]:
        """
        Parses all complete packets in the buffer.
        Yields (PacketHeader, memoryview_slice) with ZERO memory copies.
        """
        read_offset = 0

        while (self._bytes_in_buffer - read_offset) >= HEADER_SIZE:
            # Unpack directly from memoryview at offset without slicing strings!
            header_data = HEADER_STRUCT.unpack_from(self._view, read_offset)
            header = PacketHeader(*header_data)

            if header.magic != MAGIC_CONSTANT:
                raise ValueError(f"Corrupt wire packet: Invalid magic 0x{header.magic:08X}")

            total_packet_len = HEADER_SIZE + header.payload_len

            # Check if entire payload has arrived
            if (self._bytes_in_buffer - read_offset) < total_packet_len:
                break  # Await remaining chunk from socket

            # Extract zero-copy window into payload
            payload_start = read_offset + HEADER_SIZE
            payload_end = payload_start + header.payload_len
            payload_window = self._view[payload_start:payload_end]

            yield header, payload_window

            read_offset += total_packet_len

        # Compact buffer: Shift unprocessed bytes to the beginning
        if read_offset > 0:
            remaining = self._bytes_in_buffer - read_offset
            if remaining > 0:
                self._buffer[0:remaining] = self._buffer[read_offset : self._bytes_in_buffer]
            self._bytes_in_buffer = remaining


# Verification Driver
if __name__ == "__main__":
    parser = ZeroCopyNetworkParser()

    # Simulate assembling two binary packets into socket buffer
    payload_a = b"SYSTEM_TELEMETRY_SAMPLE_A"
    payload_b = b"CRITICAL_ALERT_PAYLOAD_B"

    raw_stream = bytearray()
    raw_stream.extend(HEADER_STRUCT.pack(MAGIC_CONSTANT, 101, 1, len(payload_a), 0x55AA))
    raw_stream.extend(payload_a)
    raw_stream.extend(HEADER_STRUCT.pack(MAGIC_CONSTANT, 102, 2, len(payload_b), 0x66BB))
    raw_stream.extend(payload_b)

    # Ingest into parser
    target_buf = parser.get_write_buffer()
    target_buf[: len(raw_stream)] = raw_stream
    parser.advance_write_pointer(len(raw_stream))

    # Parse with zero memory allocations
    for hdr, payload in parser.parse_packets():
        print(f"[*] Parsed Seq {hdr.seq_id} | Op {hdr.opcode} | Len {hdr.payload_len}")
        print(f"    Payload Content: {bytes(payload).decode('utf-8')}")
        print(f"    Buffer Address Identity: {payload.obj is parser._buffer}")
