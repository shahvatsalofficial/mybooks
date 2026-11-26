// parallelToolDispatcher.ts
export interface RawToolCall {
  id: string;
  name: string;
  arguments: string;
}

export interface ToolExecutionResult {
  toolCallId: string;
  name: string;
  output: string;
  durationMs: number;
  success: boolean;
}

export class ParallelToolOrchestrator {
  private handlers: Map<string, (args: any) => Promise<any>> = new Map();

  public registerTool(name: string, fn: (args: any) => Promise<any>) {
    this.handlers.set(name, fn);
  }

  public async executeBatch(calls: RawToolCall[], timeoutMs: number = 8000): Promise<ToolExecutionResult[]> {
    const promises = calls.map(async (call) => {
      const start = Date.now();
      try {
        const handler = this.handlers.get(call.name);
        if (!handler) {
          throw new Error(`Tool '${call.name}' is not registered in runtime.`);
        }
        const parsedArgs = JSON.parse(call.arguments);
        
        // Execute with timeout race
        const resultPromise = handler(parsedArgs);
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
        );
        
        const result = await Promise.race([resultPromise, timeoutPromise]);
        
        return {
          toolCallId: call.id,
          name: call.name,
          output: JSON.stringify(result),
          durationMs: Date.now() - start,
          success: true
        };
      } catch (err: any) {
        return {
          toolCallId: call.id,
          name: call.name,
          output: JSON.stringify({ error: err.message || 'Execution error' }),
          durationMs: Date.now() - start,
          success: false
        };
      }
    });

    return Promise.all(promises);
  }
}
