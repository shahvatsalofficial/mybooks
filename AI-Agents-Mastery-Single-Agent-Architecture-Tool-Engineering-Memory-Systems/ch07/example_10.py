class EloTournamentManager:
    def __init__(self, initial_rating: float = 1200.0, k_factor: float = 32.0):
        self.ratings: Dict[str, float] = {}
        self.initial = initial_rating
        self.k = k_factor

    def get_rating(self, candidate: str) -> float:
        return self.ratings.get(candidate, self.initial)

    def record_match(self, model_a: str, model_b: str, winner: str):
        ra = self.get_rating(model_a)
        rb = self.get_rating(model_b)
        
        ea = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
        eb = 1.0 - ea
        
        sa = 1.0 if winner == model_a else (0.5 if winner == "draw" else 0.0)
        sb = 1.0 - sa
        
        self.ratings[model_a] = round(ra + self.k * (sa - ea), 1)
        self.ratings[model_b] = round(rb + self.k * (sb - eb), 1)

# Verification
elo = EloTournamentManager()
elo.record_match("Prompt_V1", "Prompt_V2", winner="Prompt_V2")
elo.record_match("Prompt_V2", "Prompt_V3", winner="Prompt_V2")
print("Prompt V1 Rating:", elo.get_rating("Prompt_V1"))
print("Prompt V2 Rating:", elo.get_rating("Prompt_V2"))
