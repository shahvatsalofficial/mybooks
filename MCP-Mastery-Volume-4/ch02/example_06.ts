import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import {
  S3Client,
  ListObjectsV2Command,
  GetObjectCommand,
  HeadObjectCommand
} from "@aws-sdk/client-s3";

const s3Client = new S3Client({
  region: process.env.AWS_REGION || "us-east-1"
});

const MAX_BYTE_WINDOW = 2 * 1024 * 1024; // 2MB max partial fetch window

const server = new Server(
  { name: "s3-explorer-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "s3_list_objects",
      description: "Lists objects in an S3 bucket with prefix filtering, delimiter scoping, and pagination.",
      inputSchema: {
        type: "object",
        properties: {
          bucket: { type: "string", description: "Target AWS S3 bucket name." },
          prefix: { type: "string", description: "Key prefix to filter objects.", default: "" },
          delimiter: { type: "string", description: "Delimiter character for folder scoping (e.g. '/').", default: "/" },
          max_keys: { type: "number", description: "Maximum keys to return (max: 100).", default: 50 }
        },
        required: ["bucket"]
      }
    },
    {
      name: "s3_read_object_range",
      description: "Reads a partial byte range from an S3 object to prevent LLM context exhaustion.",
      inputSchema: {
        type: "object",
        properties: {
          bucket: { type: "string", description: "Target AWS S3 bucket name." },
          key: { type: "string", description: "Full S3 object key." },
          start_byte: { type: "number", description: "Starting byte offset (default: 0).", default: 0 },
          length_bytes: { type: "number", description: "Length of byte window (max: 2097152 / 2MB).", default: 1048576 }
        },
        required: ["bucket", "key"]
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "s3_list_objects") {
    const bucket = String(args?.bucket);
    const prefix = String(args?.prefix || "");
    const delimiter = String(args?.delimiter || "/");
    const maxKeys = Math.min(Number(args?.max_keys) || 50, 100);

    try {
      const command = new ListObjectsV2Command({
        Bucket: bucket,
        Prefix: prefix,
        Delimiter: delimiter,
        MaxKeys: maxKeys
      });

      const response = await s3Client.send(command);

      const folders = (response.CommonPrefixes || []).map((p) => p.Prefix);
      const objects = (response.Contents || []).map((o) => ({
        key: o.Key,
        sizeBytes: o.Size,
        lastModified: o.LastModified?.toISOString(),
        storageClass: o.StorageClass
      }));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ bucket, prefix, folders, objects, isTruncated: response.IsTruncated }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `S3 List Error: ${err.message}` }] };
    }
  }

  if (name === "s3_read_object_range") {
    const bucket = String(args?.bucket);
    const key = String(args?.key);
    const startByte = Math.max(Number(args?.start_byte) || 0, 0);
    const lengthBytes = Math.min(Number(args?.length_bytes) || 1048576, MAX_BYTE_WINDOW);
    const endByte = startByte + lengthBytes - 1;

    try {
      // 1. Inspect object metadata first
      const headCmd = new HeadObjectCommand({ Bucket: bucket, Key: key });
      const head = await s3Client.send(headCmd);
      const totalSize = head.ContentLength || 0;
      const contentType = head.ContentType || "application/octet-stream";

      // 2. Execute byte-range partial fetch
      const rangeHeader = `bytes=${startByte}-${Math.min(endByte, totalSize - 1)}`;
      const getCmd = new GetObjectCommand({
        Bucket: bucket,
        Key: key,
        Range: rangeHeader
      });

      const response = await s3Client.send(getCmd);
      const stream = response.Body as NodeJS.ReadableStream;

      const chunks: Buffer[] = [];
      for await (const chunk of stream) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      }
      const dataBuffer = Buffer.concat(chunks);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              bucket,
              key,
              totalSizeBytes: totalSize,
              contentType,
              rangeFetched: rangeHeader,
              bytesReturned: dataBuffer.length,
              previewText: dataBuffer.toString("utf8")
            }, null, 2)
          }
        ]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `S3 Range Fetch Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("AWS S3 Explorer MCP Server initialized.");
}

run().catch(console.error);
