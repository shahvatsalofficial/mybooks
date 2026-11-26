# ANTI-PATTERN: Recompiling format strings
for packet in stream:
    magic, length, opcode = struct.unpack("!IIH", packet[:10])
