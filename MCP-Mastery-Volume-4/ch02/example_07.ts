import { Storage } from "@google-cloud/storage";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

const storage = new Storage({
  autoRetry: true,
  maxRetries: 3
});

const mcpServer = new Server(
  { name: "gcs-streaming-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "gcs_stream_blob",
        description: "Streams a byte-range chunk from a Google Cloud Storage object using backpressure-aware buffers.",
        inputSchema: {
          type: "object",
          properties: {
            bucket: { type: "string", description: "Google Cloud Storage bucket name." },
            blob_path: { type: "string", description: "Full blob path within bucket." },
            start_byte: { type: "number", description: "Start byte offset.", default: 0 },
            chunk_size: { type: "number", description: "Bytes to read (max: 2MB).", default: 1048576 }
          },
          required: ["bucket", "blob_path"]
        }
      }
    ]
  };
});

mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "gcs_stream_blob") {
    const bucketName = String(args?.bucket);
    const blobPath = String(args?.blob_path);
    const startByte = Math.max(Number(args?.start_byte) || 0, 0);
    const chunkSize = Math.min(Number(args?.chunk_size) || 1048576, 2 * 1024 * 1024);

    try {
      const bucket = storage.bucket(bucketName);
      const file = bucket.file(blobPath);

      const [metadata] = await file.getMetadata();
      const totalSize = Number(metadata.size || 0);

      const endByte = Math.min(startByte + chunkSize - 1, totalSize - 1);

      const text = await new Promise<string>((resolve, reject) => {
        const chunks: Buffer[] = [];
        const readStream = file.createReadStream({
          start: startByte,
          end: endByte
        });

        readStream.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
        readStream.on("error", (err) => reject(err));
        readStream.on("end", () => {
          resolve(Buffer.concat(chunks).toString("utf8"));
        });
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              bucket: bucketName,
              blob: blobPath,
              totalSizeBytes: totalSize,
              rangeRead: `${startByte}-${endByte}`,
              content: text
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `GCS Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function main() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error("GCS Streaming MCP Server running.");
}

main().catch(console.error);
