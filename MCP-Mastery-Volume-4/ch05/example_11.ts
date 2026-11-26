class GrpcClientPool {
  private pool = new Map<string, { client: grpc.Client; lastUsed: number }>();

  getClient(endpoint: string, credentials: grpc.ChannelCredentials): grpc.Client {
    const now = Date.now();
    if (this.pool.has(endpoint)) {
      const entry = this.pool.get(endpoint)!;
      entry.lastUsed = now;
      return entry.client;
    }

    const client = new grpc.Client(endpoint, credentials);
    this.pool.set(endpoint, { client, lastUsed: now });
    this.scheduleSweep();
    return client;
  }

  private scheduleSweep() {
    setInterval(() => {
      const now = Date.now();
      for (const [endpoint, entry] of this.pool.entries()) {
        if (now - entry.lastUsed > 300000) {
          entry.client.close();
          this.pool.delete(endpoint);
        }
      }
    }, 60000);
  }
}
