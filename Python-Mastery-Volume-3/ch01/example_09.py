# ANEMIC DOMAIN ANTI-PATTERN (THE ROOT CAUSE)
class InventoryItem(Base):
    __tablename__ = "inventory"
    sku = Column(String, primary_key=True)
    quantity = Column(Integer)  # Mutable public state


# INSECURE PROCEDURAL SERVICE LAYER
async def allocate_stock(sku: str, qty_to_buy: int, session: AsyncSession):
    item = await session.get(InventoryItem, sku)
    # RACE CONDITION: Read-Modify-Write cycle without invariant protection!
    if item.quantity >= qty_to_buy:
        item.quantity -= qty_to_buy  # Direct external mutation
        await session.commit()
