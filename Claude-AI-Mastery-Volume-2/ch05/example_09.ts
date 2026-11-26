// Production Patch: Paginated / Truncated Tool Output
server.tool('fetch_large_logs', 'Safely streams large logs without pipe overflow', { maxLines: z.number().default(200) }, async ({ maxLines }) => {
  const lines = getSystemLogs();
  const clamped = lines.slice(-maxLines).join('\n');
  return {
    content: [{ type: 'text', text: clamped }]
  };
});
