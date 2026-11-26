import Database from "better-sqlite3";
import path from "path";

// Initialize SQLite with WAL mode and memory concurrency
function createAgentScratchpad(dbPath: string): Database.Database {
  // Validate path is strictly within the allowed workspace sandbox
  const resolved = path.resolve(dbPath);
  if (!resolved.startsWith(path.resolve(process.env.MCP_WORKSPACE_ROOT || "/tmp/mcp"))) {
    throw new Error("Security Violation: Database path outside permitted sandbox.");
  }

  const db = new Database(resolved, { timeout: 3000 });
  db.pragma("journal_mode = WAL");
  db.pragma("synchronous = NORMAL");
  db.pragma("temp_store = MEMORY");
  db.pragma("mmap_size = 30000000000"); // 30GB memory-mapped I/O ceiling

  // Create standard agent observation tables
  db.exec(`
    CREATE TABLE IF NOT EXISTS agent_memory (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      turn_index INTEGER NOT NULL,
      key TEXT NOT NULL UNIQUE,
      content TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);

  return db;
}
