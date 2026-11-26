// THE ENTERPRISE INVARIANT PATCH
if (!broker) {
  throw new UnresolvedEntityException(
    `Broker context missing for trade ${trade.id}; aborting calculation to prevent ledger corruption.`,
    { tradeId: trade.id, timestamp: Date.now() }
  );
}
