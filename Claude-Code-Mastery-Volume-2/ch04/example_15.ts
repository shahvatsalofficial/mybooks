export function truncateOutputHeadTail(content: string, maxBytes = 32768): string {
  const byteLength = Buffer.byteLength(content, "utf8");
  if (byteLength <= maxBytes) {
    return content;
  }

  const halfQuota = Math.floor((maxBytes - 500) / 2);
  const head = content.slice(0, halfQuota);
  const tail = content.slice(content.length - halfQuota);
  const omittedBytes = byteLength - (halfQuota * 2);

  return `${head}

... [TRUNCATED: ${omittedBytes.toLocaleString()} bytes omitted to protect context window] ...

${tail}`;
}
