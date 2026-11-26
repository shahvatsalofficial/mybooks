# The Zero-Copy Architecture
raw_buffer = bytearray(10 * 1024 * 1024)
mv = memoryview(raw_buffer)

# Zero memory copies! These slices merely adjust memory pointer offsets and lengths:
header_view = mv[:64]
payload_view = mv[64:1024]
data_view = mv[1024:]
