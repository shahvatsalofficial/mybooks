import Database from "better-sqlite3";

export interface JournalEvent {
  stepIndex: number;
  eventType: "THOUGHT" | "ACTION" | "OBSERVATION" | "CHECKPOINT";
  payload: Record<string, unknown>;
  gitCommitHash?: string;
  tokenCost?: number;
}

export class DurableEventJournal {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initializeSchema();
  }

  private initializeSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        goal TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
      );

      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        step_index INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        git_hash TEXT,
        token_cost REAL DEFAULT 0.0,
        timestamp TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
      );

      CREATE INDEX IF NOT EXISTS idx_session_step ON events(session_id, step_index);
    `);
  }

  public createSession(sessionId: string, goal: string): void {
    const stmt = this.db.prepare("INSERT INTO sessions (session_id, goal, status) VALUES (?, ?, 'ACTIVE')");
    stmt.run(sessionId, goal);
  }

  public appendEvent(sessionId: string, event: JournalEvent): void {
    const stmt = this.db.prepare(`
      INSERT INTO events (session_id, step_index, event_type, payload, git_hash, token_cost)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    stmt.run(
      sessionId,
      event.stepIndex,
      event.eventType,
      JSON.stringify(event.payload),
      event.gitCommitHash || null,
      event.tokenCost || 0.0
    );
  }

  /**
   * Restores the complete historical trajectory for a session.
   */
  public restoreTrajectory(sessionId: string): JournalEvent[] {
    const stmt = this.db.prepare("SELECT step_index, event_type, payload, git_hash, token_cost FROM events WHERE session_id = ? ORDER BY step_index ASC");
    const rows = stmt.all(sessionId) as any[];
    return rows.map(r => ({
      stepIndex: r.step_index,
      eventType: r.event_type,
      payload: JSON.parse(r.payload),
      gitCommitHash: r.git_hash,
      tokenCost: r.token_cost
    }));
  }

  /**
   * Rewinds the session state to targetStepIndex, truncating all subsequent events.
   */
  public rewindSession(sessionId: string, targetStepIndex: number): string | null {
    // 1. Find the Git commit snapshot at targetStepIndex
    const findStmt = this.db.prepare("SELECT git_hash FROM events WHERE session_id = ? AND step_index = ? AND git_hash IS NOT NULL LIMIT 1");
    const row = findStmt.get(sessionId, targetStepIndex) as { git_hash?: string } | undefined;

    // 2. Delete all events beyond targetStepIndex
    const deleteStmt = this.db.prepare("DELETE FROM events WHERE session_id = ? AND step_index > ?");
    deleteStmt.run(sessionId, targetStepIndex);

    return row?.git_hash || null;
  }
}
