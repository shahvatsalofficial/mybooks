return {
  trace_id: $json.headers['x-trace-id'],
  agent_name: $json.metadata.agent_name,
  model: $json.usage.model,
  prompt_tokens: $json.usage.prompt_tokens,
  completion_tokens: $json.usage.completion_tokens,
  latency_ms: $json.metadata.duration,
  timestamp: new Date().toISOString()
};
