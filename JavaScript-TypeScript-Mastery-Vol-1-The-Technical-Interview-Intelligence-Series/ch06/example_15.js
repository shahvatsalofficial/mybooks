// legacy_payment_processor.js
// Unsafe, dynamic module with zero validation boundaries

class LegacyPaymentProcessor {
    constructor(exchangeRateAdapter) {
        this.exchangeRateAdapter = exchangeRateAdapter;
    }

    /**
     * Ingests, converts, and processes a payment payload.
     * Vulnerable to missing fields, incorrect currencies, and math errors.
     */
    processPayment(payload) {
        // Missing validation boundary. Raw payload properties are read directly from memory.
        const txId = payload.txId;
        const amount = payload.amount;
        const currency = payload.currency;
        const processor = payload.processor;

        console.log(`Ingested payload for transaction: ${txId}`);

        // Vulnerable: If amount or exchange rate is undefined, this resolves to NaN
        let processedAmount = amount;

        // Danger: Accidental conversion math without proper type safety boundaries
        if (currency !== "USD") {
            const rate = this.exchangeRateAdapter.getRate(currency, "USD");
            processedAmount = amount * rate;
        }

        // Processing payment through specific processor adapters
        let receipt;
        if (processor === "stripe") {
            receipt = this.executeStripe(txId, processedAmount);
        } else if (processor === "paypal") {
            receipt = this.executePaypal(txId, processedAmount);
        } else {
            // Vulnerable: Silent failure! If processor is unsupported, execution logs a string and returns undefined
            console.error(`Unsupported processor: ${processor}`);
        }

        return {
            status: "SUCCESS",
            transactionId: txId,
            settledAmount: processedAmount,
            receiptId: receipt ? receipt.id : null
        };
    }

    executeStripe(txId, amount) {
        // Stripe expects amount in cents. No verification that amount has been converted!
        return { id: `ch_stripe_${txId}`, settled: amount * 100 };
    }

    executePaypal(txId, amount) {
        // PayPal expects a rounded string value. No checks to prevent floating point errors!
        return { id: `ch_paypal_${txId}`, settled: amount.toFixed(2) };
    }
}

module.exports = { LegacyPaymentProcessor };
