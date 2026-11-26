// Architectural Fix: Streaming Byte Cap Guard
import QueryStream from "pg-query-stream";

const stream = client.query(new QueryStream(sanitizedSql, params));
let accumulatedBytes = 0;
const MAX_BYTE_CEILING = 256 * 1024; // 256 KB hard limit

stream.on("data", (row) => {
  const rowBuffer = Buffer.from(JSON.stringify(row));
  if (accumulatedBytes + rowBuffer.length > MAX_BYTE_CEILING) {
    stream.destroy();
    // Return payload with cursor token for subsequent tool execution
  } else {
    accumulatedBytes += rowBuffer.length;
    rows.push(row);
  }
});
