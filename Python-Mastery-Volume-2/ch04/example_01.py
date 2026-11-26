# Zero-Copy Type Reinterpretation via memoryview.cast:
raw_bytes = bytearray(b"\x00\x00\x80\x3F" * 1024)  # 1024 32-bit floats (1.0 in IEEE-754)
mv = memoryview(raw_bytes)

# Cast raw bytes directly to float array (32-bit float, 'f'):
floats_view = mv.cast("f")
print(f"First element: {floats_view[0]}")  # Output: 1.0

# In-place mutation directly mutates the underlying bytearray:
floats_view[0] = 2.5
assert raw_bytes[0:4] == b"\x00\x00\x20\x40"  # Exact IEEE-754 binary for 2.5
