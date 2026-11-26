#!/usr/bin/env node
/**
 * Enterprise AST Code Intelligence MCP Server
 * Language: TypeScript / Node.js
 * Analyzes JavaScript/TypeScript codebases with semantic AST precision
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as parser from "@babel/parser";
import traverse from "@babel/traverse";
import fs from "fs/promises";
import path from "path";

const server = new McpServer({
  name: "enterprise-ast-engine",
  version: "1.0.0"
});

// Tool: Extract exported function signatures from a file
server.tool(
  "extract_signatures",
  "Parses a TypeScript/JavaScript file into an AST and extracts all exported function and class signatures",
  {
    filePath: z.string().describe("Absolute or relative path to the TypeScript source file")
  },
  async ({ filePath }) => {
    try {
      const resolvedPath = path.resolve(filePath);
      const code = await fs.readFile(resolvedPath, "utf-8");

      const ast = parser.parse(code, {
        sourceType: "module",
        plugins: ["typescript", "jsx", "decorators-legacy"]
      });

      const symbols: Array<{ type: string; name: string; line: number; params: string[] }> = [];

      (traverse as any).default(ast, {
        ExportNamedDeclaration(nodePath: any) {
          const decl = nodePath.node.declaration;
          if (!decl) return;

          if (decl.type === "FunctionDeclaration") {
            symbols.push({
              type: "function",
              name: decl.id?.name || "anonymous",
              line: decl.loc?.start.line || 0,
              params: decl.params.map((p: any) => p.name || p.type)
            });
          } else if (decl.type === "ClassDeclaration") {
            symbols.push({
              type: "class",
              name: decl.id?.name || "anonymous",
              line: decl.loc?.start.line || 0,
              params: []
            });
          }
        }
      });

      return {
        content: [{
          type: "text",
          text: JSON.stringify({ file: filePath, totalExports: symbols.length, symbols }, null, 2)
        }]
      };
    } catch (err: any) {
      return {
        content: [{ type: "text", text: `AST PARSE ERROR in ${filePath}: ${err.message}` }],
        isError: true
      };
    }
  }
);

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[AST SERVER] Ready for semantic source analysis.");
}

run().catch((e) => {
  console.error("[FATAL]", e);
  process.exit(1);
});
