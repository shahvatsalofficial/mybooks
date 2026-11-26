# In-place zero-copy mutation
payload_view[0:4] = b"\x00\x01\x02\x03" # Modifies raw_buffer in-place!
