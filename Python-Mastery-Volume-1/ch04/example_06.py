async def stream_telemetry_batches(socket_reader: StreamReader) -> AsyncGenerator[bytes, None]:
    """Yields 64KB chunks directly from the network stream with O(1) memory."""
    try:
        while not socket_reader.at_eof():
            chunk = await socket_reader.read(65536)
            if not chunk:
                break
            yield chunk
    finally:
        logger.info("Telemetry stream reader cleanly closed.")
