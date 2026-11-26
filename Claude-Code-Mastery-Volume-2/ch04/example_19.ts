import { z } from "zod";

export const LedgerTransferSchema = z.object({
  sourceAccountId: z.string().regex(/^ACT-[0-9]{8}$/, "Account ID must match ACT-XXXXXXXX format"),
  destinationAccountId: z.string().regex(/^ACT-[0-9]{8}$/, "Account ID must match ACT-XXXXXXXX format"),
  amountCents: z.number().int().positive("Transfer amount must be a positive integer in cents"),
  currency: z.enum(["USD", "EUR", "GBP"]).default("USD"),
  idempotencyToken: z.string().uuid("Must provide a unique UUID v4 idempotency token to prevent double charging")
});

export type LedgerTransferInput = z.infer<typeof LedgerTransferSchema>;

// In-memory idempotency store (backed by Redis in production)
const PROCESSED_TRANSFERS = new Map<string, { status: string; transactionId: string; timestamp: string }>();

export async function executeLedgerTransfer(input: LedgerTransferInput): Promise<string> {
  // 1. Check Idempotency Barrier
  if (PROCESSED_TRANSFERS.has(input.idempotencyToken)) {
    const existing = PROCESSED_TRANSFERS.get(input.idempotencyToken)!;
    return `### Idempotent Replay (Duplicate Invocation Detected)\n` +
           `* **Notice:** This transaction was already processed.\n` +
           `* **Original Transaction ID:** \`${existing.transactionId}\`\n` +
           `* **Original Timestamp:** \`${existing.timestamp}\`\n` +
           `* **Status:** \`${existing.status}\``;
  }

  // 2. Prevent self-transfer
  if (input.sourceAccountId === input.destinationAccountId) {
    throw new Error("TRANSACTION_REJECTED: Source and destination accounts cannot be identical.");
  }

  // 3. Execute atomic transaction (simulated)
  const transactionId = `TXN-${Date.now()}-${Math.random().toString(36).substring(2, 7).toUpperCase()}`;
  const record = {
    status: "SETTLED",
    transactionId,
    timestamp: new Date().toISOString()
  };

  // 4. Save to Idempotency Barrier before returning
  PROCESSED_TRANSFERS.set(input.idempotencyToken, record);

  const formattedAmount = (input.amountCents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: input.currency
  });

  return `### Ledger Settlement Confirmed\n` +
         `* **Transaction ID:** \`${transactionId}\`\n` +
         `* **Amount Settled:** \`${formattedAmount}\`\n` +
         `* **Source Account:** \`${input.sourceAccountId}\`\n` +
         `* **Destination Account:** \`${input.destinationAccountId}\`\n` +
         `* **Idempotency Verified:** \`${input.idempotencyToken}\`\n` +
         `* **Timestamp:** \`${record.timestamp}\``;
}
