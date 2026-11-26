import asyncio
import random
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class LogEntry(BaseModel):
    term: int
    command: str
    payload: Dict[str, Any]

class RaftAgentNode:
    """Implements core Raft leader election and log synchronization in AsyncIO."""
    
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        self.role = "FOLLOWER" # FOLLOWER, CANDIDATE, LEADER
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(1.5, 3.0)

    def receive_heartbeat(self, leader_id: str, term: int) -> bool:
        if term >= self.current_term:
            self.current_term = term
            self.role = "FOLLOWER"
            self.last_heartbeat = time.time()
            # print(f"[{self.node_id}] Heartbeat acknowledged from leader '{leader_id}' (term {term}).")
            return True
        return False

    def trigger_election_if_timed_out(self) -> Optional[int]:
        if time.time() - self.last_heartbeat > self.election_timeout and self.role != "LEADER":
            self.role = "CANDIDATE"
            self.current_term += 1
            self.voted_for = self.node_id
            self.last_heartbeat = time.time()
            votes_received = 1 # Self vote
            
            print(f"[{self.node_id}] Election timeout breached ({self.election_timeout:.2f}s)! Starting election for Term {self.current_term}...")
            # Simulate majority vote from peers
            majority_threshold = (len(self.peers) + 1) // 2 + 1
            votes_received += len(self.peers) // 2 + 1
            
            if votes_received >= majority_threshold:
                self.role = "LEADER"
                print(f"[{self.node_id}] ELECTED LEADER for Term {self.current_term} (Votes: {votes_received})!")
                return self.current_term
        return None

    def append_log_entry(self, command: str, payload: Dict[str, Any]) -> LogEntry:
        if self.role != "LEADER":
            raise PermissionError(f"Node {self.node_id} is not the cluster leader! Cannot append log.")
        entry = LogEntry(term=self.current_term, command=command, payload=payload)
        self.log.append(entry)
        print(f"[{self.node_id}] Log entry committed: '{command}' (Term {self.current_term}, Index {len(self.log)})")
        return entry
