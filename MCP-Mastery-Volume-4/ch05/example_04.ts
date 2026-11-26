import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, Tool } from "@modelcontextprotocol/sdk/types.js";
import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import protobuf from "protobufjs";

const GRPC_TARGET_ENDPOINT = process.env.GRPC_TARGET_ENDPOINT || "localhost:50051";

// Convert Protobuf Field Types to JSON Schema Primitives
function mapProtoTypeToJsonSchemaType(type: string): string {
  switch (type) {
    case "int32":
    case "int64":
    case "uint32":
    case "uint64":
    case "sint32":
    case "sint64":
    case "fixed32":
    case "fixed64":
      return "integer";
    case "float":
    case "double":
      return "number";
    case "bool":
      return "boolean";
    case "string":
    case "bytes":
    default:
      return "string";
  }
}

export class DynamicGrpcBridge {
  private client: grpc.Client;
  private protoRoot: protobuf.Root | null = null;
  private serviceMethods = new Map<string, { serviceName: string; methodName: string; requestType: string; responseType: string }>();

  constructor(targetEndpoint: string) {
    // Initialize standard insecure or TLS gRPC channel
    const credentials = process.env.GRPC_USE_TLS === "true"
      ? grpc.credentials.createSsl()
      : grpc.credentials.createInsecure();

    this.client = new grpc.Client(targetEndpoint, credentials);
  }

  // Compile Proto Definition into MCP Tool List
  async discoverMethodsFromProtoFile(protoFilePath: string): Promise<Tool[]> {
    this.protoRoot = await protobuf.load(protoFilePath);
    const tools: Tool[] = [];
    this.serviceMethods.clear();

    // Iterate through all services in the protobuf root
    const nested = this.protoRoot.nestedArray;
    for (const item of nested) {
      if (item instanceof protobuf.Service) {
        for (const [methodName, methodObj] of Object.entries(item.methods)) {
          const toolName = `${item.name.toLowerCase()}_${methodName.toLowerCase()}`;
          const reqType = this.protoRoot.lookupType(methodObj.requestType);

          // Build JSON Schema from Protobuf message fields
          const properties: Record<string, any> = {};
          const requiredFields: string[] = [];

          for (const field of reqType.fieldsArray) {
            properties[field.name] = {
              type: mapProtoTypeToJsonSchemaType(field.type),
              description: `Protobuf field ${field.name} (${field.type})`
            };
            if (field.required) requiredFields.push(field.name);
          }

          this.serviceMethods.set(toolName, {
            serviceName: item.name,
            methodName,
            requestType: methodObj.requestType,
            responseType: methodObj.responseType
          });

          tools.push({
            name: toolName,
            description: `Invokes RPC ${item.name}.${methodName} over HTTP/2.`,
            inputSchema: {
              type: "object",
              properties,
              required: requiredFields.length > 0 ? requiredFields : undefined
            }
          });
        }
      }
    }

    return tools;
  }

  // Invoke RPC Method dynamically
  async invokeRpc(toolName: string, payload: any): Promise<any> {
    const methodMeta = this.serviceMethods.get(toolName);
    if (!methodMeta || !this.protoRoot) {
      throw new Error(`Unknown RPC method: ${toolName}`);
    }

    const path = `/${methodMeta.serviceName}/${methodMeta.methodName}`;
    const RequestType = this.protoRoot.lookupType(methodMeta.requestType);
    const ResponseType = this.protoRoot.lookupType(methodMeta.responseType);

    // Validate payload against protobuf schema
    const errMsg = RequestType.verify(payload);
    if (errMsg) throw new Error(`Protobuf validation failure: ${errMsg}`);

    const message = RequestType.create(payload);
    const serializedBuffer = Buffer.from(RequestType.encode(message).finish());

    return new Promise((resolve, reject) => {
      this.client.makeUnaryRequest(
        path,
        (arg: Buffer) => arg, // Serialize pass-through
        (arg: Buffer) => ResponseType.decode(arg), // Deserializer
        serializedBuffer,
        (err, response) => {
          if (err) return reject(new Error(`gRPC Error (${err.code}): ${err.details}`));
          resolve(response);
        }
      );
    });
  }
}
