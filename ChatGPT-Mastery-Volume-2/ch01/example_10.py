# THE CATASTROPHIC ANTI-PATTERN
   while retry_count < 3:
       try:
           return client.chat.completions.create(...)
       except Exception:
           time.sleep(2) # FIXED LINEAR SLEEP!
           retry_count += 1
   ```
   Every time thousands of requests were rejected at the gateway, they slept for exactly 2.0 seconds and slammed back into the gateway simultaneously. This created a synchronized **Thundering Herd** resonance wave. Rather than allowing the OpenAI Leaky Bucket to drain, the synchronized retries kept the bucket permanently saturated at 100% capacity.
4. **Cascading Upstream Collapse**: As HTTP requests hung waiting for retries, the internal node worker queues backed up, exhausting database connection pools and web server thread pools, ultimately knocking down the checkout service and primary cart APIs.
