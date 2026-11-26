# Stateful property testing with Hypothesis RuleBasedStateMachine
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from domain.inventory import InventoryAggregate

class InventoryStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.inventory = InventoryAggregate(sku="DESK-01", total_stock=100)

    @rule(qty=st.integers(min_value=1, max_value=20))
    def reserve_stock(self, qty: int):
        self.inventory.try_reserve(qty)

    @rule(qty=st.integers(min_value=1, max_value=20))
    def release_stock(self, qty: int):
        self.inventory.try_release(qty)

    @invariant()
    def reserved_never_exceeds_total_stock(self):
        # Invariant: Reserved stock can NEVER exceed total physical stock
        assert self.inventory.reserved_stock <= self.inventory.total_stock
        assert self.inventory.available_stock >= 0
