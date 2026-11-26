import { Kafka } from "kafkajs";
import SchemaRegistry, { SchemaType } from "@kafkajs/confluent-schema-registry";

const kafka = new Kafka({
  clientId: "mcp-event-consumer",
  brokers: (process.env.KAFKA_BROKERS || "localhost:9092").split(","),
  ssl: process.env.KAFKA_USE_SSL === "true",
  sasl: process.env.KAFKA_SASL_USER ? {
    mechanism: "scram-sha-256",
    username: process.env.KAFKA_SASL_USER,
    password: process.env.KAFKA_SASL_PASSWORD || ""
  } : undefined
});

const registry = new SchemaRegistry({
  host: process.env.SCHEMA_REGISTRY_URL || "http://localhost:8081"
});

export class KafkaMcpConsumerBridge {
  private consumer = kafka.consumer({ groupId: "mcp-agent-monitoring-group" });
  private recentMessages: { topic: string; partition: number; offset: string; payload: any; timestamp: string }[] = [];

  async initialize(topics: string[]) {
    await this.consumer.connect();
    for (const topic of topics) {
      await this.consumer.subscribe({ topic, fromBeginning: false });
    }

    await this.consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        let decodedPayload: any = null;

        if (message.value) {
          // Check for Confluent Schema Registry Magic Byte (0x00)
          if (message.value[0] === 0x00) {
            decodedPayload = await registry.decode(message.value);
          } else {
            try {
              decodedPayload = JSON.parse(message.value.toString("utf8"));
            } catch {
              decodedPayload = message.value.toString("utf8");
            }
          }
        }

        const event = {
          topic,
          partition,
          offset: message.offset,
          payload: decodedPayload,
          timestamp: new Date(Number(message.timestamp)).toISOString()
        };

        this.recentMessages.push(event);
        if (this.recentMessages.length > 100) this.recentMessages.shift(); // Keep rolling 100 messages
      }
    });
  }

  getRecentEvents(topicFilter?: string, limit: number = 20) {
    let events = this.recentMessages;
    if (topicFilter) {
      events = events.filter((e) => e.topic === topicFilter);
    }
    return events.slice(-limit);
  }

  async disconnect() {
    await this.consumer.disconnect();
  }
}
