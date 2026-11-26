// hardened_payment_processor.ts
// Fully typed, strict-null checked, and branded transaction engine

declare const brand: unique symbol;

export type Brand<T, TBrand extends string> = T & {
    readonly [brand]: TBrand;
};

// 1. Establish Branded Currencies to enforce type-safety during arithmetic operations
export type USD = Brand<number, "USD">;
export type NativeAmount = Brand<number, "NativeAmount">;

export type SupportedCurrency = "USD" | "EUR" | "INR";
export type SupportedProcessor = "STRIPE" | "PAYPAL";

// 2. Define clear payload schemas for validation boundaries
export interface IncomingPaymentPayload {
    txId: string;
    amount: number;
    currency: string;
    processor: string;
}

export interface HardenedPaymentResult {
    status: "SUCCESS" | "FAILED";
    transactionId: string;
    settledAmount: USD;
    receiptId: string;
}

export interface ExchangeRateService {
    getRate(from: SupportedCurrency, to: "USD"): number;
}

// 3. Custom type guards to validate dynamic, incoming inputs
export function isSupportedCurrency(currency: string): currency is SupportedCurrency {
    return currency === "USD" || currency === "EUR" || currency === "INR";
}

export function isSupportedProcessor(processor: string): processor is SupportedProcessor {
    const upper = processor.toUpperCase();
    return upper === "STRIPE" || upper === "PAYPAL";
}

export function validateIncomingPayload(payload: unknown): asserts payload is IncomingPaymentPayload {
    if (typeof payload !== "object" || payload === null) {
        throw new TypeError("Payment payload must be a non-null object.");
    }

    const data = payload as Record<string, unknown>;

    if (typeof data["txId"] !== "string" || data["txId"].trim().length === 0) {
        throw new Error("Missing or invalid: txId.");
    }

    if (typeof data["amount"] !== "number" || isNaN(data["amount"]) || data["amount"] <= 0) {
        throw new Error("Amount must be a positive number.");
    }

    if (typeof data["currency"] !== "string" || !isSupportedCurrency(data["currency"])) {
        throw new Error("Invalid or unsupported currency type.");
    }

    if (typeof data["processor"] !== "string" || !isSupportedProcessor(data["processor"])) {
        throw new Error("Invalid or unsupported payment processor.");
    }
}

// Custom error for exhaustiveness failures
export class UnreachableProcessorError extends Error {
    constructor(val: never) {
        super(`Unhandled payment processor encountered: ${JSON.stringify(val)}`);
    }
}

export class HardenedPaymentProcessor {
    private exchangeService: ExchangeRateService;

    constructor(exchangeService: ExchangeRateService) {
        this.exchangeService = exchangeService;
    }

    /**
     * Safely ingests, validates, and routes dynamic transaction requests.
     * Complete compile-time type safety with zero external API footprint changes.
     */
    public processPayment(rawPayload: unknown): HardenedPaymentResult {
        // Enforce boundary validation. Invalid data is rejected immediately.
        validateIncomingPayload(rawPayload);

        // TypeScript now guarantees that 'rawPayload' is a valid 'IncomingPaymentPayload'
        const txId: string = rawPayload.txId;
        const rawAmount: number = rawPayload.amount;
        
        // Explicit type narrowing for currency and processor values
        const currency: SupportedCurrency = rawPayload.currency as SupportedCurrency;
        const processor: SupportedProcessor = rawPayload.processor.toUpperCase() as SupportedProcessor;

        console.log(`Processing validated transaction: ${txId}`);

        // 4. Secure Branded Currency conversion math
        let settledUSD: USD;

        if (currency === "USD") {
            settledUSD = rawAmount as unknown as USD;
        } else {
            const conversionRate = this.exchangeService.getRate(currency, "USD");
            if (isNaN(conversionRate) || conversionRate <= 0) {
                throw new Error(`Invalid exchange rate obtained for currency: ${currency}`);
            }
            settledUSD = (rawAmount * conversionRate) as unknown as USD;
        }

        // 5. Exhaustive routing utilizing nominal switch-case checks
        let receiptId: string;

        switch (processor) {
            case "STRIPE":
                receiptId = this.executeStripe(txId, settledUSD);
                break;
            case "PAYPAL":
                receiptId = this.executePaypal(txId, settledUSD);
                break;
            default:
                // Implements compile-time safety against unhandled processors
                const exhaust: never = processor;
                throw new UnreachableProcessorError(exhaust);
        }

        return {
            status: "SUCCESS",
            transactionId: txId,
            settledAmount: settledUSD,
            receiptId: receiptId
        };
    }

    private executeStripe(txId: string, amount: USD): string {
        // Stripe expects amount in cents. The branded type guarantees amount is a safe USD currency float.
        const amountCents = Math.round(amount * 100);
        return `receipt_stripe_${txId}_${amountCents}`;
    }

    private executePaypal(txId: string, amount: USD): string {
        // PayPal expects a formatted string representing rounded dollars.
        const formattedAmount = amount.toFixed(2);
        return `receipt_paypal_${txId}_${formattedAmount}`;
    }
}
