# eval_recorder.py
"""
Evaluation result recorder — persists agent evaluation records to ClickHouse
for dashboard querying and trend analysis.
"""
import time
from dataclasses import dataclass, asdict
from typing import Optional
import clickhouse_connect


@dataclass
class EvalRecord:
    timestamp: float
    agent_version: str
    prompt_version: str
    session_id: str
    query: str
    response: str
    accuracy: float
    relevance: float
    coherence: float
    safety: float
    overall: float
    latency_ms: float
    tool_calls_made: int
    was_rollback_triggered: bool = False
    environment: str = "production"


class EvalRecorder:
    def __init__(self, clickhouse_host: str, database: str = "agent_evals"):
        self.client = clickhouse_connect.get_client(host=clickhouse_host)
        self.database = database
        self._ensure_table()

    def _ensure_table(self):
        self.client.command(f"""
            CREATE TABLE IF NOT EXISTS {self.database}.eval_records (
                timestamp Float64,
                agent_version String,
                prompt_version String,
                session_id String,
                query String,
                response String,
                accuracy Float32,
                relevance Float32,
                coherence Float32,
                safety Float32,
                overall Float32,
                latency_ms Float32,
                tool_calls_made UInt8,
                was_rollback_triggered Bool,
                environment String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, agent_version)
        """)

    def record(self, eval_record: EvalRecord):
        self.client.insert(
            f"{self.database}.eval_records",
            [list(asdict(eval_record).values())],
            column_names=list(asdict(eval_record).keys())
        )
