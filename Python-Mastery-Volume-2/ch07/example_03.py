"""
Recipe 07.1: SIMD-Aligned NumPy C-Array Allocator with Zero-Copy Views
Architecture: 64-byte cache-line aligned buffer allocator for AVX-512 SIMD operations.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import ctypes
import numpy as np
from typing import Tuple


def allocate_simd_aligned_array(
    shape: Tuple[int, ...],
    dtype: np.dtype = np.float64,
    alignment: int = 64,
) -> np.ndarray:
    """Allocates a NumPy array aligned to cache line boundaries (64 bytes for AVX-512).
    
    Args:
        shape: Tuple of dimension lengths.
        dtype: NumPy data type (default float64).
        alignment: Memory alignment boundary in bytes (64 for AVX-512, 32 for AVX2).
        
    Returns:
        Zero-copy NumPy ndarray mapped over the aligned raw C memory pointer.
    """
    dtype = np.dtype(dtype)
    total_elements = int(np.prod(shape))
    total_bytes = total_elements * dtype.itemsize

    # Allocate padding to guarantee alignment offset
    raw_buffer = (ctypes.c_char * (total_bytes + alignment))()
    raw_address = ctypes.addressof(raw_buffer)

    # Compute offset to next aligned address boundary
    offset = (alignment - (raw_address % alignment)) % alignment
    aligned_address = raw_address + offset

    # Wrap aligned memory address in ctypes array pointer
    c_type_map = {
        np.dtype(np.float64): ctypes.c_double,
        np.dtype(np.float32): ctypes.c_float,
        np.dtype(np.int64): ctypes.c_int64,
        np.dtype(np.int32): ctypes.c_int32,
    }
    c_element_type = c_type_map.get(dtype, ctypes.c_char)
    c_array_type = c_element_type * total_elements

    # Map typed pointer over aligned address
    aligned_c_array = c_array_type.from_address(aligned_address)

    # Zero-copy conversion to NumPy ndarray
    arr = np.frombuffer(aligned_c_array, dtype=dtype).reshape(shape)

    # Pin raw_buffer to prevent garbage collection while array is in use
    arr._base_memory_anchor = raw_buffer  # type: ignore[attr-defined]

    return arr


# Demonstration & Verification
if __name__ == "__main__":
    matrix = allocate_simd_aligned_array(shape=(1024, 1024), dtype=np.float64, alignment=64)
    data_pointer = matrix.ctypes.data

    print(f"Allocated Matrix Shape: {matrix.shape}")
    print(f"Memory Address:        0x{data_pointer:016X}")
    print(f"Alignment Verification: Address % 64 == {data_pointer % 64} (0 indicates exact 64-byte alignment)")
    assert data_pointer % 64 == 0, "Memory alignment check failed!"

    # Verify write and calculation
    matrix.fill(1.25)
    assert matrix[0, 0] == 1.25
    print("SIMD-aligned memory buffer successfully initialized and verified.")
