// tests/escrow.spec.ts (Shallow assertion)
it('should release escrow funds', () => {
  const engine = new EscrowEngine();
  const res = engine.releaseFunds(1000, 0.05);
  expect(res.status).toBe('SUCCESS'); // Tautological: does not verify fee calculation!
});
