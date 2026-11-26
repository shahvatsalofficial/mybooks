function ingestWebhook(rawPayload: unknown) {
    // Before assertion, rawPayload is completely locked as 'unknown'
    // rawPayload.transactionId -> Compilation Error!

    assertPaymentPayload(rawPayload);

    // After assertion passes, rawPayload is narrowed to 'PaymentPayload' for the rest of the block
    console.log(`Ingested metric: ${rawPayload.transactionId} has value ${rawPayload.amount}`);
}
