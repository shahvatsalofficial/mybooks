/**
 * Filename: mcp_handshake_engine.ts
 * Description: Client-side capability negotiation and lifecycle handshake manager.
 * Author: Vatsal Shah (MCP Mastery Series)
 * Dependencies: @modelcontextprotocol/sdk, zod
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { z } from "zod";

// Schema defining required enterprise server capabilities
const ServerCapabilityRequirements = z.object({
  resources: z
    .object({
      subscribe: z.boolean().optional(),
      listChanged: z.boolean().optional(),
    })
    .optional(),
  tools: z
    .object({
      listChanged: z.boolean().optional(),
    })
    .optional(),
  prompts: z.object({}).optional(),
});

export interface HandshakeConfig {
  command: string;
  args: string[];
  env?: Record<string, string>;
  timeoutMs: number;
  maxRetries: number;
}

export class MCPHandshakeEngine {
  private client: Client;
  private transport: StdioClientTransport | null = null;
  private config: HandshakeConfig;

  constructor(config: HandshakeConfig) {
    this.config = config;
    this.client = new Client(
      {
        name: "EnterpriseArchitectClient",
        version: "1.0.0",
      },
      {
        capabilities: {
          roots: {
            listChanged: true,
          },
          sampling: {},
        },
      }
    );
  }

  /**
   * Spawns sub-process, binds stdio transport, and executes handshake.
   */
  public async connectWithRetry(): Promise<void> {
    let attempts = 0;
    let delay = 500; // ms

    while (attempts < this.config.maxRetries) {
      try {
        attempts++;
        console.log(`[Handshake] Initiating connection attempt ${attempts}/${this.config.maxRetries}...`);
        
        await this.executeConnection();
        console.log(`[Handshake] Successfully connected and negotiated capabilities with server.`);
        return;
      } catch (error) {
        console.error(`[Handshake] Attempt ${attempts} failed:`, error);
        await this.cleanup();

        if (attempts >= this.config.maxRetries) {
          throw new Error(
            `[Handshake Critical] Failed to negotiate connection after ${this.config.maxRetries} attempts. Aborting.`
          );
        }

        console.log(`[Handshake] Waiting ${delay}ms before next retry...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * 2, 5000); // Exponential backoff with 5s ceiling
      }
    }
  }

  private async executeConnection(): Promise<void> {
    this.transport = new StdioClientTransport({
      command: this.config.command,
      args: this.config.args,
      env: this.config.env || process.env,
    });

    // Enforce connection timeout boundary
    const connectPromise = this.client.connect(this.transport);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(
        () => reject(new Error(`Handshake timed out after ${this.config.timeoutMs}ms`)),
        this.config.timeoutMs
      )
    );

    await Promise.race([connectPromise, timeoutPromise]);

    // Inspect negotiated capabilities
    const serverCaps = this.client.getServerCapabilities();
    const serverInfo = this.client.getServerVersion();

    console.log(`[Handshake] Remote Server Identified: ${serverInfo?.name} v${serverInfo?.version}`);
    
    // Strict schema audit of remote capabilities
    const validation = ServerCapabilityRequirements.safeParse(serverCaps);
    if (!validation.success) {
      throw new Error(`[Handshake Rejection] Server capability schema invalid: ${validation.error.message}`);
    }

    console.log("[Handshake] Server verified against enterprise governance baseline.");
  }

  public async cleanup(): Promise<void> {
    if (this.transport) {
      try {
        await this.transport.close();
      } catch (err) {
        console.warn("[Handshake] Warning during transport teardown:", err);
      }
      this.transport = null;
    }
  }

  public getClient(): Client {
    return this.client;
  }
}
