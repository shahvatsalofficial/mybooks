/**
 * Enterprise TypeScript Assistants API v2 Streaming Engine
 * Implements full typed event handling and tool submission.
 */
import OpenAI from "openai";
import { Response } from "express";

const openai = new OpenAI();

export async function streamAssistantToHttpResponse(
  threadId: string,
  assistantId: string,
  userMessage: string,
  res: Response
): Promise<void> {
  // Step 1: Append user message to persistent thread
  await openai.beta.threads.messages.create(threadId, {
    role: "user",
    content: userMessage
  });

  // Step 2: Configure SSE HTTP headers
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive"
  });

  // Step 3: Launch streaming run
  const stream = openai.beta.threads.runs.stream(threadId, {
    assistant_id: assistantId,
    max_prompt_tokens: 10000,
    max_completion_tokens: 2000
  });

  stream
    .on("textCreated", () => {
      res.write("event: text_start\ndata: {}\n\n");
    })
    .on("textDelta", (textDelta) => {
      if (textDelta.value) {
        res.write(`event: delta\ndata: ${JSON.stringify({ text: textDelta.value })}\n\n`);
      }
    })
    .on("toolCallCreated", (toolCall) => {
      res.write(`event: tool_start\ndata: ${JSON.stringify({ type: toolCall.type })}\n\n`);
    })
    .on("event", async (event) => {
      if (event.event === "thread.run.requires_action") {
        const run = event.data;
        const toolCalls = run.required_action?.submit_tool_outputs.tool_calls || [];
        
        // Execute tool handlers
        const toolOutputs = await Promise.all(
          toolCalls.map(async (tc) => {
            if (tc.function.name === "fetch_stock_quote") {
              const args = JSON.parse(tc.function.arguments);
              return {
                tool_call_id: tc.id,
                output: JSON.stringify({ ticker: args.ticker, price: 185.50 })
              };
            }
            return {
              tool_call_id: tc.id,
              output: JSON.stringify({ error: "Unsupported tool" })
            };
          })
        );

        // Submit tool outputs and attach new stream back to response
        const toolStream = openai.beta.threads.runs.submitToolOutputsStream(
          threadId,
          run.id,
          { tool_outputs: toolOutputs }
        );

        toolStream.on("textDelta", (delta) => {
          if (delta.value) {
            res.write(`event: delta\ndata: ${JSON.stringify({ text: delta.value })}\n\n`);
          }
        });

        toolStream.on("end", () => {
          res.write("event: done\ndata: [DONE]\n\n");
          res.end();
        });
      }
    })
    .on("end", () => {
      res.write("event: done\ndata: [DONE]\n\n");
      res.end();
    })
    .on("error", (error) => {
      console.error("[Stream Error]:", error);
      res.write(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`);
      res.end();
    });
}
