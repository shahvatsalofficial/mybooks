// Production Graceful Teardown Pattern in Custom MCP Clients
async function terminateClientSafely(client: Client, transport: StdioClientTransport): Promise<void> {
  console.log("[Lifecycle] Initiating graceful client shutdown...");

  // Register clean timeout guard
  const shutdownTimeout = setTimeout(() => {
    console.error("[Lifecycle WARNING] Child server did not exit in 3000ms. Forcing SIGKILL.");
    if (transport.process && !transport.process.killed) {
      transport.process.kill("SIGKILL");
    }
  }, 3000);

  try {
    // 1. Close high-level client session (emits protocol notifications)
    await client.close();
    // 2. Close low-level stdio transport (terminates streams)
    await transport.close();
    clearTimeout(shutdownTimeout);
    console.log("[Lifecycle] Server child process terminated cleanly.");
  } catch (err: any) {
    clearTimeout(shutdownTimeout);
    console.error(`[Lifecycle Error] Error during teardown: ${err.message}`);
    if (transport.process && !transport.process.killed) {
      transport.process.kill("SIGKILL");
    }
  }
}
