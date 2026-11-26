CREATE TABLE transactional_outbox (
       id UUID PRIMARY KEY,
       aggregate_type VARCHAR(64) NOT NULL,
       aggregate_id VARCHAR(64) NOT NULL,
       event_type VARCHAR(128) NOT NULL,
       payload JSONB NOT NULL,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```
2. **Atomic Local Commit**: When a business entity is updated, the domain event is inserted into `transactional_outbox` within the *exact same local database transaction*:
   ```typescript
   await db.transaction(async (trx) => {
     await trx('orders').insert(orderData);
     await trx('transactional_outbox').insert({
       id: uuidv4(),
       aggregate_type: 'Order',
       aggregate_id: orderData.id,
       event_type: 'OrderCreated',
       payload: JSON.stringify(orderData),
     });
   });
   ```
3. **CDC Event Relay**: A Change Data Capture daemon (such as Debezium tailing the Postgres WAL) tails the `transactional_outbox` table and publishes events to Apache Kafka with guaranteed at-least-once delivery, decoupling domain state mutations from network message brokers.

---

## 5.4 Automated REST-to-gRPC Interface Synthesis & Protocol Buffer Evolution

Legacy microservices frequently communicate via internal HTTP/1.1 REST APIs with JSON payloads. While REST/JSON is ergonomically friendly for human developers, it introduces severe operational bottlenecks in high-throughput enterprise systems:
* **Serialization Overhead**: Parsing JSON strings requires extensive CPU cycles, string allocations, and garbage collection overhead.
* **Lack of Strict Typing**: JSON payloads are unstructured text. A client can send an integer where a string is expected, triggering runtime type errors that are not caught at compile time.
* **Head-of-Line Blocking**: HTTP/1.1 requires establishing separate TCP connections or pipelining requests sequentially over a single socket.

To achieve maximum throughput and strict contract enforcement, enterprise modernization agents autonomously refactor internal service interfaces from **REST/JSON to gRPC / Protocol Buffers (Protobuf)**.

### Protocol Buffer Contract Synthesis
The autonomous agent parses the legacy service’s OpenAPI / Swagger specification or TypeScript interfaces and synthesizes strongly typed Protocol Buffer definitions:
