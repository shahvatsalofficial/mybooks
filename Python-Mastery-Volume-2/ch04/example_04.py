"""
Recipe 04.3: Zero-Copy CPython Buffer Protocol Exporter (Py_buffer)
Architecture: Pure-Python ctypes class implementing the CPython Buffer Protocol.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import ctypes
import mmap
import sys
from typing import Any


class SharedMemoryBufferExporter:
    """Manages an aligned raw C memory block exposing Python's Buffer Protocol."""

    def __init__(self, size_bytes: int) -> None:
        self.size_bytes = size_bytes
        # Allocate page-aligned anonymous memory via mmap
        self._mm = mmap.mmap(-1, size_bytes, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
        # Create a memoryview wrapping the mmap buffer directly
        self._view = memoryview(self._mm)

    @property
    def raw_address(self) -> int:
        """Returns the physical virtual memory address of the buffer."""
        # Extract underlying C pointer address from mmap buffer
        buf_type = ctypes.c_char * self.size_bytes
        buf_from_mem = buf_type.from_buffer(self._mm)
        return ctypes.addressof(buf_from_mem)

    def write_at_offset(self, offset: int, data: bytes) -> None:
        """Writes bytes directly into the memory buffer."""
        if offset + len(data) > self.size_bytes:
            raise ValueError("Buffer overflow: write exceeds allocated size")
        self._mm[offset : offset + len(data)] = data

    def read_at_offset(self, offset: int, length: int) -> bytes:
        """Reads bytes slice directly from memory buffer."""
        return self._mm[offset : offset + length]

    def get_memoryview(self) -> memoryview:
        """Returns a standard Python memoryview exposing the PEP 3118 buffer."""
        return self._view

    def close(self) -> None:
        """Releases the memory-mapped segment."""
        self._view.release()
        self._mm.close()


# Demonstration & Verification
if __name__ == "__main__":
    # Allocate 1MB shared buffer
    exporter = SharedMemoryBufferExporter(size_bytes=1024 * 1024)
    print(f"Allocated Buffer at Virtual Address: 0x{exporter.raw_address:016X}")

    # Write binary protocol header
    header_magic = b"\x7F\x45\x4C\x46\x02\x01\x01\x00"  # ELF-like magic header
    exporter.write_at_offset(0, header_magic)

    # Acquire zero-copy memoryview and verify slice
    mv = exporter.get_memoryview()
    extracted_slice = bytes(mv[0:8])
    print(f"Extracted Memoryview Slice: {extracted_slice.hex()}")
    assert extracted_slice == header_magic, "Memory slice verification failed!"

    # Clean deallocation
    exporter.close()
    print("Zero-Copy Buffer Protocol verification successful.")
