# REMEDIATED TEST USING DOCKER TESTCONTAINERS
async def test_fractional_shares_precision_on_real_postgres(db_session: AsyncSession):
    # Executes against real PostgreSQL 16 container!
    trade = TradeAllocationModel(
        allocated_shares=Decimal("12.54321098"),
        share_price=Decimal("105.25"),
    )
    db_session.add(trade)
    await db_session.commit()

    # Re-fetch from real database engine: Proves PostgreSQL schema preserves scale!
    refetched = await db_session.get(TradeAllocationModel, trade.id)
    assert refetched.allocated_shares == Decimal("12.54321098")
