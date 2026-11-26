// FLAWED PRODUCTION CODE: Unbounded buffer accumulation
upstreamStream.on('data', (chunk) => {
  // res.write() returns false when client socket buffer is full!
  // Flawed code completely ignored the return value and pushed all bytes
  res.write(chunk); 
});
