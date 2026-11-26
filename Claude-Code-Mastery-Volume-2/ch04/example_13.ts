const TransferFundsSchema = z.object({
  sourceAccount: z.string(),
  destinationAccount: z.string(),
  amountCents: z.number().int().positive(),
  idempotencyKey: z.string().uuid("Mandatory UUID v4 idempotency token")
});
