# DEFECTIVE INLINE PROCESSING LOOP (PRE-INCIDENT)
async for msg in consumer:
    # CRITICAL ARCHITECTURAL FLAW:
    # Executing slow external network calls sequentially inside the Kafka poll loop!
    for item in msg.value["subscriptions"]:
        # If the payment gateway takes 800ms per call, 500 records take 400 SECONDS!
        # This exceeded 'max_poll_interval_ms = 300,000' (300 seconds / 5 minutes).
        await payment_gateway.charge(item["user_id"], item["amount"])
    
    await consumer.commit()
