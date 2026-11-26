import hashlib

class AuditTrailEntry(BaseModel):
    timestamp: float
    graph_name: str
    node_name: str
    state_delta_hash: str
    previous_entry_hash: str

class SwarmAuditLedger:
    def __init__(self):
        self.ledger: List[AuditTrailEntry] = []

    def record_transition(self, graph_name: str, node_name: str, state_delta: Dict[str, Any]):
        prev_hash = self.ledger[-1].state_delta_hash if self.ledger else "GENESIS_BLOCK"
        delta_str = json.dumps(state_delta, sort_keys=True)
        curr_hash = hashlib.sha256(f"{delta_str}:{prev_hash}".encode()).hexdigest()
        
        entry = AuditTrailEntry(
            timestamp=time.time(),
            graph_name=graph_name,
            node_name=node_name,
            state_delta_hash=curr_hash,
            previous_entry_hash=prev_hash
        )
        self.ledger.append(entry)
