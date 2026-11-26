/**
 * recipe_3_4_distributed_subscription_hub.ts
 * Multi-node distributed MCP Resource Invalidation Hub using Redis Pub/Sub.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import Redis from 'ioredis';

export class DistributedSubscriptionHub {
  private pub: Redis;
  private sub: Redis;
  private localSubscribers = new Map<string, Set<SSEServerTransport>>();
  private channelName = 'mcp:resource:invalidations';

  constructor(redisUrl: string = 'redis://localhost:6379') {
    this.pub = new Redis(redisUrl);
    this.sub = new Redis(redisUrl);
    this.setupRedisListener();
  }

  private setupRedisListener(): void {
    this.sub.subscribe(this.channelName, (err) => {
      if (err) console.error('[Redis Sub Error]', err);
    });

    this.sub.on('message', (channel, message) => {
      if (channel !== this.channelName) return;
      try {
        const { uri } = JSON.parse(message);
        this.broadcastLocal(uri);
      } catch (err) {
        console.error('[Malformed Invalidation Message]', err);
      }
    });
  }

  /**
   * Register a local client connection's subscription to a URI
   */
  public subscribe(uri: string, transport: SSEServerTransport): void {
    if (!this.localSubscribers.has(uri)) {
      this.localSubscribers.set(uri, new Set());
    }
    this.localSubscribers.get(uri)!.add(transport);

    // Clean up when client disconnects
    transport.onclose = () => {
      const set = this.localSubscribers.get(uri);
      if (set) {
        set.delete(transport);
        if (set.size === 0) this.localSubscribers.delete(uri);
      }
    };
  }

  /**
   * Publish an invalidation event across the entire server cluster
   */
  public async publishInvalidation(uri: string): Promise<void> {
    const payload = JSON.stringify({ uri, timestamp: Date.now() });
    await this.pub.publish(this.channelName, payload);
  }

  /**
   * Broadcast notifications/resources/updated to locally attached clients
   */
  private broadcastLocal(uri: string): void {
    const clients = this.localSubscribers.get(uri);
    if (!clients || clients.size === 0) return;

    for (const transport of clients) {
      try {
        // Construct MCP protocol JSON-RPC notification frame
        const notification = {
          jsonrpc: '2.0',
          method: 'notifications/resources/updated',
          params: { uri },
        };
        transport.send(notification);
      } catch (err) {
        console.error('[Broadcast Failure]', err);
      }
    }
  }

  public async shutdown(): Promise<void> {
    await this.sub.quit();
    await this.pub.quit();
    this.localSubscribers.clear();
  }
}
