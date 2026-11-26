class ConsensusChoice(BaseModel):
    choice_id: str
    description: str

class BordaConsensusEngine:
    @staticmethod
    def calculate_winner(ballots: List[List[str]]) -> str:
        """
        Calculates consensus winner using Borda count.
        ballots: List of ranked choice_id lists, highest preference first.
        """
        scores: Dict[str, int] = {}
        for ballot in ballots:
            num_choices = len(ballot)
            for rank, choice in enumerate(ballot):
                # Points: highest preference gets (num_choices - 1), lowest gets 0
                points = (num_choices - 1) - rank
                scores[choice] = scores.get(choice, 0) + points
        
        # Sort descending by total points
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        print(f"[CONSENSUS] Final Borda Scores: {ranked}")
        return ranked[0][0] # Winner choice_id
