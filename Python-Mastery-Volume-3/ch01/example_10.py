# REMEDIATED CLEAN DOMAIN AGGREGATE
@dataclass(slots=True)
class InventoryAggregate:
    sku: SkuId
    available_quantity: int
    version: int  # Optimistic concurrency token

    def allocate(self, quantity: int) -> None:
        if quantity <= 0:
            raise InvariantViolationError("Allocation quantity must be positive.")
        if self.available_quantity < quantity:
            raise InsufficientStockError(
                f"Requested {quantity} units, but only {self.available_quantity} available."
            )
        # Enforce invariant transition
        self.available_quantity -= quantity
        self.version += 1
