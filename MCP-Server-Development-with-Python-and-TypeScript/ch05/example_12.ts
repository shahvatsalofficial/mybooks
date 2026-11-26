/**
 * recipe_5_3_reverse_sampling_server.ts
 * Advanced MCP Server demonstrating server-initiated LLM reverse sampling.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  CreateMessageResultSchema,
  McpError,
  ErrorCode,
} from '@modelcontextprotocol/sdk/types.js';

const server = new Server(
  { name: 'autonomous-indexing-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'index_and_summarize_document',
        description: 'Analyzes a document, using dynamic client sampling to extract a concise abstract.',
        inputSchema: {
          type: 'object',
          properties: {
            document_text: { type: 'string', description: 'Raw text content to analyze.' },
          },
          required: ['document_text'],
          additionalProperties: false,
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name !== 'index_and_summarize_document') {
    throw new McpError(ErrorCode.MethodNotFound, `Tool '${name}' not found.`);
  }

  const documentText = args?.document_text as string;
  console.error('[Server] Initiating reverse sampling request to client host...');

  try {
    // INVERSION OF CONTROL: Request LLM generation from client host
    const samplingResponse = await server.request(
      {
        method: 'sampling/createMessage',
        params: {
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: `Summarize this text in exactly 2 clear sentences for an indexing catalog:\n\n${documentText}`,
              },
            },
          ],
          modelPreferences: {
            hints: [{ name: 'claude-3-5-haiku' }, { name: 'gpt-4o-mini' }],
            costPriority: 0.8,
            speedPriority: 0.9,
            intelligencePriority: 0.5,
          },
          systemPrompt: 'You are an ultra-fast indexing assistant. Return only the 2-sentence summary.',
          maxTokens: 150,
          temperature: 0.0,
        },
      },
      CreateMessageResultSchema
    );

    const summaryText =
      samplingResponse.content.type === 'text'
        ? samplingResponse.content.text
        : 'Summary generation failed.';

    console.error(`[Server] Received sampled summary from model: ${samplingResponse.model}`);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              status: 'indexed',
              model_used: samplingResponse.model,
              extracted_summary: summaryText,
              char_count: documentText.length,
            },
            null,
            2
          ),
        },
      ],
      isError: false,
    };
  } catch (err: any) {
    console.error('[Sampling Failed]', err);
    return {
      content: [
        {
          type: 'text',
          text: `SamplingError: Client host refused or failed sampling request: ${err.message}`,
        },
      ],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('[Indexing Server] Online and ready for reverse sampling.');
}

main().catch(console.error);
