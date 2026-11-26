export type PaymentProcessor = "STRIPE" | "PAYPAL" | "ADYEN";

export class UnreachableCaseError extends Error {
    constructor(val: never) {
        super(`Unreachable case hit for value: ${JSON.stringify(val)}`);
    }
}

function getProcessorEndpoint(processor: PaymentProcessor): string {
    switch (processor) {
        case "STRIPE":
            return "https://api.stripe.com/v3/charges";
        case "PAYPAL":
            return "https://api.paypal.com/v2/payments";
        case "ADYEN":
            return "https://api.adyen.com/v67/payments";
        default:
            // If any processor type is omitted, the compiler throws an error here.
            // TypeScript detects that the 'processor' variable has not been narrowed to 'never'.
            throw new UnreachableCaseError(processor);
    }
}
