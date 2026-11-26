export interface PaymentPayload {
    transactionId: string;
    amount: number;
    currency: "USD" | "EUR" | "INR";
}

export function isPaymentPayload(payload: unknown): payload is PaymentPayload {
    if (typeof payload !== "object" || payload === null) {
        return false;
    }

    // Narrowing properties on an unknown object structure safely
    const data = payload as Record<string, unknown>;

    const hasValidTxId = typeof data["transactionId"] === "string" && data["transactionId"].trim().length > 0;
    const hasValidAmount = typeof data["amount"] === "number" && !isNaN(data["amount"]) && data["amount"] > 0;
    const hasValidCurrency = data["currency"] === "USD" || data["currency"] === "EUR" || data["currency"] === "INR";

    return hasValidTxId && hasValidAmount && hasValidCurrency;
}
