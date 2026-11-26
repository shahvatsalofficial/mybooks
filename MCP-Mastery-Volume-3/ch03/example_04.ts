// otel_middleware.ts — Production OpenTelemetry Middleware for MCP
import { trace, context, SpanStatusCode, Span, propagation } from '@opentelemetry/api';

const tracer = trace.getTracer('mcp-gateway-tracer', '1.0.0');

export interface McpJsonRpcRequest {
    jsonrpc: '2.0';
    id: string | number;
    method: string;
    params: {
        name: string;
        arguments: Record<string, any>;
        _meta?: Record<string, any>;
    };
}

export class OtelMcpMiddleware {
    /**
     * Executes a tool invocation wrapped in a distributed OpenTelemetry span
     */
    public static async traceToolExecution<T>(
        request: McpJsonRpcRequest,
        tenantId: string,
        modelName: string,
        executor: (span: Span) => Promise<T>
    ): Promise<T> {
        // 1. Extract incoming W3C traceparent from _meta or generate fresh context
        const parentHeader = request.params._meta?.traceparent;
        const activeContext = parentHeader
            ? propagation.extract(context.active(), { traceparent: parentHeader })
            : context.active();

        const toolName = request.params.name;
        const spanName = `mcp.tool_call:${toolName}`;

        return tracer.startActiveSpan(
            spanName,
            {
                attributes: {
                    'mcp.tool.name': toolName,
                    'mcp.rpc.method': request.method,
                    'mcp.rpc.id': String(request.id),
                    'tenant.id': tenantId,
                    'gen_ai.model': modelName,
                    'rpc.system': 'jsonrpc',
                    'rpc.service': 'mcp-gateway'
                }
            },
            activeContext,
            async (span: Span) => {
                const startTime = Date.now();
                try {
                    // Inject current active span context into downstream _meta
                    const carrier: Record<string, string> = {};
                    propagation.inject(context.active(), carrier);
                    if (!request.params._meta) request.params._meta = {};
                    request.params._meta.traceparent = carrier.traceparent;

                    span.addEvent('tool_dispatch_started', {
                        timestamp: startTime,
                        arguments_keys: Object.keys(request.params.arguments || {}).join(',')
                    });

                    // Execute the underlying tool microservice call
                    const result = await executor(span);

                    const durationMs = Date.now() - startTime;
                    span.setAttribute('mcp.duration_ms', durationMs);
                    span.setStatus({ code: SpanStatusCode.OK });
                    span.addEvent('tool_dispatch_completed', { duration_ms: durationMs });

                    return result;
                } catch (error: any) {
                    const durationMs = Date.now() - startTime;
                    span.setAttribute('mcp.duration_ms', durationMs);
                    span.recordException(error);
                    span.setStatus({
                        code: SpanStatusCode.ERROR,
                        message: error.message || 'Tool execution failure'
                    });
                    throw error;
                } finally {
                    span.end();
                }
            }
        );
    }
}
