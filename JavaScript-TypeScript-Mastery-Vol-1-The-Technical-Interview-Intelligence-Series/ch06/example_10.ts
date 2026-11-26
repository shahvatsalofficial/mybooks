function processIncomingData(rawPayload: unknown) {
    if (isPaymentPayload(rawPayload)) {
        // Safe: TypeScript has narrowed 'rawPayload' to 'PaymentPayload'.
        // You can now access properties with absolute type safety.
        console.log(`Processing Transaction: ${rawPayload.transactionId.toUpperCase()}`);
    } else {
        // Safe: Compile-time check holds. Payload is rejected as malformed.
        console.error("Malformed payload rejected at application boundary.");
    }
}
