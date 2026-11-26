/**
 * recipe_5_2_dynamic_prompts.ts
 * Enterprise TypeScript Prompt Provider with argument schema validation.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';

interface PromptDefinition {
  name: string;
  description: string;
  arguments: Array<{ name: string; description: string; required: boolean }>;
  handler: (args: Record<string, string>) => Promise<any[]>;
}

const PROMPT_REGISTRY: Map<string, PromptDefinition> = new Map();

// Register a production prompt
PROMPT_REGISTRY.set('generate_meeting_memo', {
  name: 'generate_meeting_memo',
  description: 'Converts raw audio transcripts into executive decision memos.',
  arguments: [
    { name: 'transcript_uri', description: 'URI of the transcript resource.', required: true },
    { name: 'executive_summary_only', description: 'Boolean flag: true or false.', required: false },
  ],
  handler: async (args) => {
    const isSummaryOnly = args.executive_summary_only === 'true';

    return [
      {
        role: 'user',
        content: {
          type: 'text',
          text: `You are an Executive Chief of Staff. Transform the meeting transcript at ${args.transcript_uri} into an executive decision memo. Focus on key strategic deliverables, responsible owners, and firm deadlines. Summary only mode: ${isSummaryOnly}.`,
        },
      },
    ];
  },
});

const server = new Server(
  { name: 'prompts-server', version: '1.0.0' },
  { capabilities: { prompts: {} } }
);

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  const prompts = Array.from(PROMPT_REGISTRY.values()).map((p) => ({
    name: p.name,
    description: p.description,
    arguments: p.arguments,
  }));
  return { prompts };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: rawArgs } = request.params;
  const def = PROMPT_REGISTRY.get(name);

  if (!def) {
    throw new McpError(ErrorCode.MethodNotFound, `Prompt '${name}' does not exist.`);
  }

  // Validate required arguments
  for (const argDef of def.arguments) {
    if (argDef.required && (!rawArgs || !rawArgs[argDef.name])) {
      throw new McpError(
        ErrorCode.InvalidParams,
        `Missing required argument '${argDef.name}' for prompt '${name}'.`
      );
    }
  }

  const messages = await def.handler(rawArgs || {});
  return {
    description: def.description,
    messages,
  };
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[Prompts Server] Running on stdio.');
}

main().catch(console.error);
