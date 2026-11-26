from typing import List, Dict

class MapReduceMemoryCompactor:
    def __init__(self, batch_size: int = 4):
        self.batch_size = batch_size

    def compress_dialogue_chunk(self, chunk: List[Dict[str, str]]) -> str:
        # Extracts user goals, decisions made, and unresolved blockers
        users = [msg['content'] for msg in chunk if msg['role'] == 'user']
        assistants = [msg['content'] for msg in chunk if msg['role'] == 'assistant']
        return f"Goals: {'; '.join(users[:2])} | Actions: {'; '.join(assistants[:2])}"

    def compact_memory(self, history: List[Dict[str, str]]) -> str:
        summaries = []
        for i in range(0, len(history), self.batch_size):
            chunk = history[i:i + self.batch_size]
            summaries.append(self.compress_dialogue_chunk(chunk))
        return " \n---\n ".join(summaries)

compactor = MapReduceMemoryCompactor(batch_size=2)
msgs = [
    {"role": "user", "content": "Set up PostgreSQL cluster on AWS"},
    {"role": "assistant", "content": "Created Aurora Postgres instance in us-east-1"},
    {"role": "user", "content": "Enable pgvector extension"},
    {"role": "assistant", "content": "Executed CREATE EXTENSION vector"}
]
summary = compactor.compact_memory(msgs)
print("Abstractive Memory Summary:\n", summary)
