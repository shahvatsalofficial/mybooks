function detectFileType(buffer: Buffer): string {
  if (buffer.length < 4) return "unknown";
  if (buffer.subarray(0, 4).toString("utf8") === "%PDF") return "application/pdf";
  if (buffer[0] === 0x89 && buffer.subarray(1, 4).toString("utf8") === "PNG") return "image/png";
  if (buffer[0] === 0x50 && buffer[1] === 0x4B && buffer[2] === 0x03 && buffer[3] === 0x04) return "application/zip";
  return "application/octet-stream";
}
