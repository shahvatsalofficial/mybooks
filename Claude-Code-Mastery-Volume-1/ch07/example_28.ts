// Hardened tests/escrow.spec.ts
it('should strictly compute escrow fee deductions and invariant balances', () => {
  const engine = new EscrowEngine();
  const amount = 1000;
  const feeRatio = 0.05;
  const res = engine.releaseFunds(amount, feeRatio);

  expect(res.status).toBe('SUCCESS');
  expect(res.fee).toBe(50.0);
  expect(res.netAmount).toBe(950.0);
  expect(res.netAmount + res.fee).toBe(amount); // Mathematical conservation invariant
});
