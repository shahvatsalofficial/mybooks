# Eliminate Nagle buffering stalls immediately upon connection
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
