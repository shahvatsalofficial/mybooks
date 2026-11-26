// Production Patch: Native Backpressure Flow Control
upstreamStream.on('data', (chunk) => {
  const canContinueWriting = res.write(chunk);
  if (!canContinueWriting) {
    // Socket buffer is full! Pause upstream producer to stop memory bloat
    upstreamStream.pause();
    // Wait until client drains its socket buffer before resuming
    res.once('drain', () => {
      upstreamStream.resume();
    });
  }
});
