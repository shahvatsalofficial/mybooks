import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool
} from "@modelcontextprotocol/sdk/types.js";
import crypto from "crypto";
import fs from "fs";
import path from "path";

const VAULT_ROOT = path.resolve(process.env.VAULT_ROOT_DIR || "./secure_vault");
const MASTER_SECRET = process.env.VAULT_MASTER_KEY || "insecure-default-change-in-production-32b!";

// Ensure vault directory exists
if (!fs.existsSync(VAULT_ROOT)) {
  fs.mkdirSync(VAULT_ROOT, { recursive: true, mode: 0o700 });
}

// Key Derivation: Derive 256-bit key using HKDF with SHA-256
function deriveEncryptionKey(salt: Buffer): Buffer {
  return crypto.hkdfSync("sha256", MASTER_SECRET, salt, "mcp-vault-v1", 32);
}

// Strict Path Traversal Assertion (Chroot Jail)
function assertInsideVault(requestedPath: string): string {
  const resolved = path.resolve(VAULT_ROOT, requestedPath);
  if (!resolved.startsWith(VAULT_ROOT)) {
    throw new Error(`Security Violation: Path traversal detected outside vault: ${requestedPath}`);
  }
  return resolved;
}

// Encrypt plaintext buffer to binary vault format: [Salt:16][IV:12][Tag:16][Ciphertext:N]
function encryptBuffer(plaintext: Buffer): Buffer {
  const salt = crypto.randomBytes(16);
  const iv = crypto.randomBytes(12);
  const key = deriveEncryptionKey(salt);

  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();

  return Buffer.concat([salt, iv, tag, ciphertext]);
}

// Decrypt vault binary format with authentication tag verification
function decryptBuffer(encryptedPayload: Buffer): Buffer {
  if (encryptedPayload.length < 44) {
    throw new Error("Corrupted vault file: Payload smaller than cryptographic header.");
  }

  const salt = encryptedPayload.subarray(0, 16);
  const iv = encryptedPayload.subarray(16, 28);
  const tag = encryptedPayload.subarray(28, 44);
  const ciphertext = encryptedPayload.subarray(44);

  const key = deriveEncryptionKey(salt);
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);

  return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}

const server = new Server(
  { name: "secure-vault-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: Tool[] = [
    {
      name: "vault_write_secret",
      description: "Encrypts and stores a text secret into a named file inside the secure directory vault.",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Relative file path inside vault (e.g. 'credentials/stripe.txt')." },
          content: { type: "string", description: "Plaintext content to encrypt and store." }
        },
        required: ["filename", "content"]
      }
    },
    {
      name: "vault_read_secret",
      description: "Decrypts and reads a stored secret from the vault with memory zeroization.",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Relative file path inside vault." }
        },
        required: ["filename"]
      }
    },
    {
      name: "vault_list_files",
      description: "Lists all encrypted files currently stored inside the directory vault.",
      inputSchema: {
        type: "object",
        properties: {
          subfolder: { type: "string", description: "Optional subfolder inside vault.", default: "" }
        }
      }
    }
  ];
  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "vault_write_secret") {
    const filename = String(args?.filename);
    const content = String(args?.content);

    try {
      const fullPath = assertInsideVault(filename);
      const dir = path.dirname(fullPath);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true, mode: 0o700 });

      const plaintextBuf = Buffer.from(content, "utf8");
      const encryptedBuf = encryptBuffer(plaintextBuf);
      
      // Zero out plaintext buffer in memory immediately
      plaintextBuf.fill(0);

      fs.writeFileSync(fullPath, encryptedBuf);

      return {
        content: [{ type: "text", text: `Successfully encrypted and stored '${filename}' (${encryptedBuf.length} bytes on disk).` }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Vault Write Error: ${err.message}` }] };
    }
  }

  if (name === "vault_read_secret") {
    const filename = String(args?.filename);

    try {
      const fullPath = assertInsideVault(filename);
      if (!fs.existsSync(fullPath)) {
        return { isError: true, content: [{ type: "text", text: `File '${filename}' does not exist in vault.` }] };
      }

      const encryptedPayload = fs.readFileSync(fullPath);
      const decryptedBuf = decryptBuffer(encryptedPayload);
      const plaintextResult = decryptedBuf.toString("utf8");

      // Memory Zeroization Guard
      decryptedBuf.fill(0);

      return {
        content: [{ type: "text", text: plaintextResult }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Vault Read Error: ${err.message}` }] };
    }
  }

  if (name === "vault_list_files") {
    const subfolder = String(args?.subfolder || "");
    try {
      const targetDir = assertInsideVault(subfolder);
      if (!fs.existsSync(targetDir)) {
        return { content: [{ type: "text", text: JSON.stringify([], null, 2) }] };
      }

      const files = fs.readdirSync(targetDir, { recursive: true });
      return {
        content: [{ type: "text", text: JSON.stringify(files, null, 2) }]
      };
    } catch (err: any) {
      return { isError: true, content: [{ type: "text", text: `Vault List Error: ${err.message}` }] };
    }
  }

  throw new Error(`Tool ${name} not found`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Secure Vault MCP Server initialized on stdio transport.");
}

run().catch(console.error);
