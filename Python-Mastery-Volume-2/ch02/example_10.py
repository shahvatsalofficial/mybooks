# FLAW IN PRODUCTION NORMALIZER:
from functools import cached_property

class InstrumentContract:
    @cached_property
    def volatility_surface(self) -> Matrix:
        # Expensive DB call: takes ~120ms to query and compute
        return db_client.load_surface(self.ticker)
