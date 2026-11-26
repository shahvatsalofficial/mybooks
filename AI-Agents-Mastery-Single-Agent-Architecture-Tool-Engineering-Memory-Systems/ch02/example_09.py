import sqlite3

class SQLiteStateJournal:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS state_journal (
                turn INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                current_state TEXT NOT NULL,
                transition_reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def record_transition(self, session_id: str, state: str, reason: str):
        with self.conn:
            self.conn.execute(
                "INSERT INTO state_journal (session_id, current_state, transition_reason) VALUES (?, ?, ?)",
                (session_id, state, reason)
            )

    def fetch_history(self, session_id: str) -> List[Tuple[int, str, str]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT turn, current_state, transition_reason FROM state_journal WHERE session_id = ? ORDER BY turn ASC", (session_id,))
        return cursor.fetchall()

# Verification
journal = SQLiteStateJournal()
journal.record_transition("sess_101", "INIT", "User opened session")
journal.record_transition("sess_101", "AUTH", "API token verified")
journal.record_transition("sess_101", "EXEC", "Dispatched payment batch")
print("Journaled State Turns:", len(journal.fetch_history("sess_101")))
