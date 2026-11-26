# PRODUCTION PATTERN: Pre-compiled Struct Engine
HEADER_PARSER = struct.Struct("!IIH") # Compiled C descriptor

for packet in stream:
    # 3x-5x faster: Direct invocation of pre-compiled C function
    magic, length, opcode = HEADER_PARSER.unpack_from(packet, offset=0)
