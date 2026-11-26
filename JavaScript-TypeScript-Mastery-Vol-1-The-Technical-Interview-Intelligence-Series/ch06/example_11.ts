export function assertPaymentPayload(payload: unknown): asserts payload is PaymentPayload {
    if (typeof payload !== "object" || payload === null) {
        throw new TypeError("Payload must be a non-null object.");
    }

    const data = payload as Record<string, unknown>;

    if (typeof data["transactionId"] !== "string" || data["transactionId"].trim().length === 0) {
        throw new Error("Missing or invalid string: transactionId.");
    }

    if (typeof data["amount"] !== "number" || isNaN(data["amount"]) || data["amount"] <= 0) {
        throw new Error("Missing or invalid positive number: amount.");
    }

    const currency = data["currency"];
    if (currency !== "USD" && currency !== "EUR" && currency !== "INR") {
        throw new Error("Invalid or unsupported currency value.");
    }
}
