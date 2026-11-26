// Production Security Patch: Strip external images from AI Markdown rendering
export function sanitizeMcpMarkdown(rawMarkdown: string): string {
  // Strip all image tags: ![alt](url) -> [Image Blocked]
  return rawMarkdown.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '[Embedded Image Blocked by Enterprise Security Policy]');
}
