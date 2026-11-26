/**
 * recipe_4_4_tool_dag_executor.ts
 * Multi-tool dependency graph executor for autonomous MCP agent workflows.
 */

export interface ToolNode {
  id: string;
  toolName: string;
  arguments: Record<string, any>;
  dependencies: string[]; // List of upstream ToolNode IDs required before execution
}

export interface ExecutionResult {
  nodeId: string;
  toolName: string;
  output: any;
  isError: boolean;
}

export class ToolDagExecutor {
  constructor(private mcpClient: any) {}

  /**
   * Execute a collection of dependent tool nodes in topological order.
   */
  public async executeDag(nodes: ToolNode[]): Promise<Map<string, ExecutionResult>> {
    const results = new Map<string, ExecutionResult>();
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const inDegree = new Map<string, number>();
    const adjacency = new Map<string, string[]>();

    // Initialize graph structures
    for (const node of nodes) {
      inDegree.set(node.id, node.dependencies.length);
      adjacency.set(node.id, []);
    }

    for (const node of nodes) {
      for (const depId of node.dependencies) {
        if (!nodeMap.has(depId)) {
          throw new Error(`Invalid DAG: Dependency '${depId}' required by '${node.id}' does not exist.`);
        }
        adjacency.get(depId)!.push(node.id);
      }
    }

    // Kahn's Algorithm: Queue nodes with zero dependencies
    const readyQueue: string[] = [];
    for (const [id, degree] of inDegree.entries()) {
      if (degree === 0) readyQueue.push(id);
    }

    let processedCount = 0;

    while (readyQueue.length > 0) {
      // Execute available independent nodes in parallel
      const currentBatch = [...readyQueue];
      readyQueue.length = 0;

      const batchPromises = currentBatch.map(async (nodeId) => {
        const node = nodeMap.get(nodeId)!;
        
        // 1. Interpolate parameters from upstream outputs
        const resolvedArgs = this.interpolateArguments(node.arguments, results);

        // 2. Dispatch tools/call via MCP client
        try {
          const callResponse = await this.mcpClient.request(
            {
              method: 'tools/call',
              params: {
                name: node.toolName,
                arguments: resolvedArgs,
              },
            },
            CallToolResultSchema
          );

          const isError = Boolean(callResponse.isError);
          const firstContent = callResponse.content?.[0];
          const parsedOutput = firstContent?.type === 'text' ? firstContent.text : callResponse.content;

          return {
            nodeId,
            toolName: node.toolName,
            output: parsedOutput,
            isError,
          };
        } catch (err: any) {
          return {
            nodeId,
            toolName: node.toolName,
            output: `ProtocolExecutionFailure: ${err.message}`,
            isError: true,
          };
        }
      });

      const batchResults = await Promise.all(batchPromises);

      for (const res of batchResults) {
        results.set(res.nodeId, res);
        processedCount++;

        // If a node failed with isError, dependent children cannot safely proceed
        if (!res.isError) {
          for (const neighborId of adjacency.get(res.nodeId)!) {
            inDegree.set(neighborId, inDegree.get(neighborId)! - 1);
            if (inDegree.get(neighborId) === 0) {
              readyQueue.push(neighborId);
            }
          }
        } else {
          console.error(`[DAG] Node '${res.nodeId}' failed. Aborting dependent children: ${adjacency.get(res.nodeId)!.join(', ')}`);
        }
      }
    }

    if (processedCount < nodes.length) {
      console.warn(`[DAG] Warning: Only ${processedCount}/${nodes.length} nodes executed. Unexecuted nodes were blocked by failures or cycles.`);
    }

    return results;
  }

  /**
   * Replace $steps.<nodeId>.<property> references with actual upstream outputs
   */
  private interpolateArguments(args: Record<string, any>, results: Map<string, ExecutionResult>): Record<string, any> {
    const serialized = JSON.stringify(args);
    const interpolated = serialized.replace(/\"\$steps\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_.-]+)\"/g, (_, stepId, path) => {
      const stepResult = results.get(stepId);
      if (!stepResult || stepResult.isError) return 'null';
      
      try {
        const data = typeof stepResult.output === 'string' ? JSON.parse(stepResult.output) : stepResult.output;
        const val = path.split('.').reduce((acc: any, key: string) => acc?.[key], data);
        return JSON.stringify(val ?? null);
      } catch {
        return JSON.stringify(stepResult.output);
      }
    });

    return JSON.parse(interpolated);
  }
}
