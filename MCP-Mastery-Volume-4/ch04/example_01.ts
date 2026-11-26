import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import Docker from "dockerode";

const docker = new Docker({ socketPath: process.env.DOCKER_SOCKET_PATH || "/var/run/docker.sock" });

const server = new Server(
  { name: "docker-proxy-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Privilege Escalation Guard
function assertSafeContainerConfig(config: any) {
  if (config.Privileged === true) {
    throw new Error("Security Violation: Privileged containers are strictly forbidden.");
  }
  if (config.HostConfig?.Privileged === true) {
    throw new Error("Security Violation: HostConfig.Privileged is strictly forbidden.");
  }
  if (Array.isArray(config.HostConfig?.Binds)) {
    for (const bind of config.HostConfig.Binds) {
      if (bind.startsWith("/:") || bind.startsWith("/etc") || bind.startsWith("/var/run")) {
        throw new Error(`Security Violation: Unsafe host bind mount detected: '${bind}'.`);
      }
    }
  }
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "docker_list_containers",
      description: "Lists active or all Docker containers with status, ports, and image tags.",
      inputSchema: {
        type: "object",
        properties: {
          all: { type: "boolean", description: "Include stopped containers.", default: false }
        }
      }
    },
    {
      name: "docker_inspect_container",
      description: "Returns compact health, state, and resource limits for a specific container.",
      inputSchema: {
        type: "object",
        properties: {
          container_id: { type: "string", description: "Container name or hex ID." }
        },
        required: ["container_id"]
      }
    },
    {
      name: "docker_get_container_logs",
      description: "Retrieves the last N lines of demultiplexed stdout/stderr logs from a container.",
      inputSchema: {
        type: "object",
        properties: {
          container_id: { type: "string", description: "Container name or ID." },
          tail: { type: "number", description: "Number of lines from end of log (max: 100).", default: 50 }
        },
        required: ["container_id"]
      }
    },
    {
      name: "docker_restart_container",
      description: "Gracefully restarts a container with a 10-second timeout.",
      inputSchema: {
        type: "object",
        properties: {
          container_id: { type: "string", description: "Container name or ID." }
        },
        required: ["container_id"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "docker_list_containers") {
    const all = Boolean(args?.all);
    try {
      const containers = await docker.listContainers({ all });
      const summary = containers.map((c) => ({
        id: c.Id.substring(0, 12),
        names: c.Names.map((n) => n.replace(/^\//, "")),
        image: c.Image,
        state: c.State,
        status: c.Status,
        ports: c.Ports.map((p) => `${p.PrivatePort}:${p.PublicPort || "none"}/${p.Type}`)
      }));

      return {
        content: [{ type: "text", text: JSON.stringify(summary, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Docker List Error: ${err.message}` }] };
    }
  }

  if (name === "docker_inspect_container") {
    const containerId = String(args?.container_id);
    try {
      const container = docker.getContainer(containerId);
      const data = await container.inspect();

      const compactData = {
        id: data.Id.substring(0, 12),
        name: data.Name.replace(/^\//, ""),
        created: data.Created,
        state: {
          status: data.State.Status,
          running: data.State.Running,
          exitCode: data.State.ExitCode,
          error: data.State.Error,
          startedAt: data.State.StartedAt,
          finishedAt: data.State.FinishedAt,
          health: data.State.Health?.Status || "No healthcheck"
        },
        restartCount: data.RestartCount,
        image: data.Config.Image,
        memoryLimitBytes: data.HostConfig.Memory,
        cpuQuota: data.HostConfig.CpuQuota
      };

      return {
        content: [{ type: "text", text: JSON.stringify(compactData, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Docker Inspect Error: ${err.message}` }] };
    }
  }

  if (name === "docker_get_container_logs") {
    const containerId = String(args?.container_id);
    const tail = Math.min(Number(args?.tail) || 50, 100);

    try {
      const container = docker.getContainer(containerId);
      const logBuffer = (await container.logs({
        stdout: true,
        stderr: true,
        tail,
        timestamps: true
      })) as Buffer;

      // Demux Docker log stream: Docker prefixes each frame with an 8-byte header
      let cleanLog = "";
      let offset = 0;
      while (offset < logBuffer.length) {
        if (offset + 8 > logBuffer.length) break;
        const streamType = logBuffer.readUInt8(offset); // 1 = stdout, 2 = stderr
        const frameSize = logBuffer.readUInt32BE(offset + 4);
        offset += 8;

        if (offset + frameSize > logBuffer.length) break;
        const frameContent = logBuffer.subarray(offset, offset + frameSize).toString("utf8");
        const prefix = streamType === 2 ? "[STDERR] " : "";
        cleanLog += `${prefix}${frameContent}`;
        offset += frameSize;
      }

      // Fallback if log was not multiplexed
      if (!cleanLog && logBuffer.length > 0) {
        cleanLog = logBuffer.toString("utf8");
      }

      return {
        content: [{ type: "text", text: cleanLog || "No logs available." }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Docker Log Error: ${err.message}` }] };
    }
  }

  if (name === "docker_restart_container") {
    const containerId = String(args?.container_id);
    try {
      const container = docker.getContainer(containerId);
      await container.restart({ t: 10 });
      return {
        content: [{ type: "text", text: `Container '${containerId}' restarted successfully.` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Docker Restart Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Docker Proxy MCP Server running on stdio.");
}

main().catch(console.error);
