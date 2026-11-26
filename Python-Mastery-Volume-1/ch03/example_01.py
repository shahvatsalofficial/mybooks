# The Naive Memory-Copying Trap
chunk = socket.recv(10 * 1024 * 1024) # 10MB heap allocation
header = chunk[:64]                   # ALLOCATES NEW 64-byte bytes object!
payload = chunk[64:1024]              # ALLOCATES NEW 960-byte bytes object!
data = chunk[1024:]                   # ALLOCATES NEW ~9.99MB bytes object!
