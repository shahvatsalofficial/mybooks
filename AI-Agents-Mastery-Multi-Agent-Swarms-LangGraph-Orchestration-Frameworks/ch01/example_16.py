class BFTVote(BaseModel):
    agent_id: str
    decision: Literal["APPROVE", "REJECT", "ABSTAIN"]
    signature: str
    rationale: str

class ByzantineConsensusEngine:
    def __init__(self, total_agents: int = 4):
        self.total_agents = total_agents
        # Maximum tolerable Byzantine (malicious or broken) agents: f = (N - 1) // 3
        self.max_byzantine_faults = (total_agents - 1) // 3
        self.quorum_threshold = (2 * self.max_byzantine_faults) + 1

    def evaluate_bft_quorum(self, votes: List[BFTVote]) -> Dict[str, Any]:
        print(f"[BFT ENGINE] Evaluating {len(votes)} votes (N={self.total_agents}, Quorum={self.quorum_threshold}, Max Faults={self.max_byzantine_faults})...")
        tally: Dict[str, int] = {"APPROVE": 0, "REJECT": 0, "ABSTAIN": 0}
        
        for vote in votes:
            tally[vote.decision] = tally.get(vote.decision, 0) + 1

        print(f"[BFT TALLY] Approve: {tally['APPROVE']}, Reject: {tally['REJECT']}, Abstain: {tally['ABSTAIN']}")
        
        if tally["APPROVE"] >= self.quorum_threshold:
            return {"verdict": "BYZANTINE_CONSENSUS_APPROVE", "confidence": tally["APPROVE"] / len(votes)}
        elif tally["REJECT"] >= self.quorum_threshold:
            return {"verdict": "BYZANTINE_CONSENSUS_REJECT", "confidence": tally["REJECT"] / len(votes)}
        else:
            return {"verdict": "BYZANTINE_DISAGREEMENT_ESCALATE", "confidence": 0.0}
