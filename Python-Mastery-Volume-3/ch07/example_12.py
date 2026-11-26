# PRODUCTION POSTGRESQL MODEL
class TradeAllocationModel(Base):
    __tablename__ = "trade_allocations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    # CRITICAL PRODUCTION SCHEMA FLAW:
    # Column defined as Numeric without scale/precision, defaulting to scale 0 in PostgreSQL!
    # In PostgreSQL, NUMERIC without arguments acts as NUMERIC(dynamic) or NUMERIC(precision, 0)
    # depending on migration state, coercing "12.5432" to "12"!
    allocated_shares: Mapped[Decimal] = mapped_column(Numeric)
