import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";

const server = new McpServer({
  name: "cloud-storage-mcp",
  version: "1.0.0"
});

// Define an RFC 6570 URI Template matching storage buckets and file paths
const s3FileTemplate = new ResourceTemplate(
  "s3://{bucket}/{+path}",
  { list: undefined } // Indicates dynamic resource pattern
);

// Register resource handler
server.resource(
  "s3-object-viewer",
  s3FileTemplate,
  {
    description: "Reads raw text or telemetry files stored in enterprise S3 buckets",
    mimeType: "text/plain"
  },
  async (uri, { bucket, path }) => {
    // Parameters 'bucket' and 'path' are automatically parsed from the URI!
    console.error(`[AUDIT] Reading S3 bucket: ${bucket}, key: ${path}`);
    
    const fileContent = await fetchObjectFromS3(bucket, path);
    
    return {
      contents: [
        {
          uri: uri.href,
          text: fileContent,
          mimeType: "text/plain"
        }
      ]
    };
  }
);
