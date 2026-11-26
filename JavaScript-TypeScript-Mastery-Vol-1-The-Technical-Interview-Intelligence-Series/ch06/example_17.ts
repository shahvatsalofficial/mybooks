// hardened_payment_processor.test.ts
// Diagnostic validation suite for currency conversion and validation safety

import { 
    HardenedPaymentProcessor, 
    ExchangeRateService, 
    IncomingPaymentPayload 
} from "./hardened_payment_processor";

describe("HardenedPaymentProcessor Boundary Audit", () => {
    let mockExchangeService: Jest.Mocked<ExchangeRateService>;
    let processor: HardenedPaymentProcessor;

    beforeEach(() => {
        mockExchangeService = {
            getRate: jest.fn()
        };
        processor = new HardenedPaymentProcessor(mockExchangeService);
    });

    test("Ingesting a valid payload should process successfully", () => {
        mockExchangeService.getRate.mockReturnValue(0.012); // INR to USD exchange rate

        const validPayload = {
            txId: "tx_98765",
            amount: 1000,
            currency: "INR",
            processor: "stripe"
        };

        const result = processor.processPayment(validPayload);

        expect(result.status).toBe("SUCCESS");
        expect(result.transactionId).toBe("tx_98765");
        expect(result.settledAmount).toBe(12); // 1000 * 0.012 = 12 USD
        expect(result.receiptId).toBe("receipt_stripe_tx_98765_1200"); // 12 USD = 1200 Cents
    });

    test("Payload with missing or invalid txId must be rejected", () => {
        const invalidPayload = {
            amount: 100,
            currency: "USD",
            processor: "stripe"
        };

        expect(() => {
            processor.processPayment(invalidPayload);
        }).toThrow("Missing or invalid: txId.");
    });

    test("Payload with negative amounts should trigger immediately validation error", () => {
        const invalidPayload = {
            txId: "tx_1111",
            amount: -50.00,
            currency: "USD",
            processor: "stripe"
        };

        expect(() => {
            processor.processPayment(invalidPayload);
        }).toThrow("Amount must be a positive number.");
    });

    test("Payload with unsupported currency must fail validation", () => {
        const invalidPayload = {
            txId: "tx_2222",
            amount: 50.00,
            currency: "GBP", // GBP is unsupported by our system
            processor: "stripe"
        };

        expect(() => {
            processor.processPayment(invalidPayload);
        }).toThrow("Invalid or unsupported currency type.");
    });

    test("Payload with unsupported processor must fail validation", () => {
        const invalidPayload = {
            txId: "tx_3333",
            amount: 50.00,
            currency: "USD",
            processor: "braintree"
        };

        expect(() => {
            processor.processPayment(invalidPayload);
        }).toThrow("Invalid or unsupported payment processor.");
    });
});
