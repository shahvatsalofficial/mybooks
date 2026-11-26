// server.js - Production Graceful Draining Handler
const http = require('http');
const server = http.createServer(app);

let isShuttingDown = false;

// Health check endpoint immediately fails once SIGTERM is received
app.get('/healthz', (req, res) => {
  if (isShuttingDown) {
    return res.status(503).json({ status: 'DRAINING', message: 'Server is terminating' });
  }
  return res.status(200).json({ status: 'HEALTHY' });
});

process.on('SIGTERM', () => {
  console.log('[SIGTERM] Received termination signal. Starting graceful socket draining...');
  isShuttingDown = true;

  // Stop accepting new connections
  server.close((err) => {
    if (err) {
      console.error('[SIGTERM] Error during socket closure:', err);
      process.exit(1);
    }
    console.log('[SIGTERM] All active connections drained cleanly. Terminating process.');
    process.exit(0);
  });

  // Force shutdown if connections do not close within 45 seconds
  setTimeout(() => {
    console.error('[SIGTERM] Forced shutdown timeout reached. Terminating forcefully.');
    process.exit(1);
  }, 45000);
});
