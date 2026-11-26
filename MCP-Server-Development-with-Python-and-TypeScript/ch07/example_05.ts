res.on('close', () => {
     sessions.delete(transport.sessionId);
   });
   ```
   Failing to execute this cleanup results in catastrophic file descriptor and memory leaks.

### Edge Computing: Running MCP on Hono & Cloudflare Workers

While Express remains common for Node.js microservices running in traditional Docker containers, modern agent architectures increasingly deploy to **Edge Isolates** (such as Cloudflare Workers, Deno Deploy, or Fastly Compute@Edge).

In edge environments, running a heavy Node.js runtime with hundreds of megabytes of resident memory is impractical. The **Hono** framework provides an ultra-lightweight, standards-compliant web framework with sub-millisecond cold starts and a 3 MB baseline memory footprint.

Using Hono's `streamSSE` helper, developers can implement MCP Server-Sent Events without relying on Node.js-specific `http.ServerResponse` objects:
