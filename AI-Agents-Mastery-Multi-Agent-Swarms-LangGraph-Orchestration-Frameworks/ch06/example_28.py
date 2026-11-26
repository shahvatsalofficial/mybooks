class AMQPLatencyHistogramExporter:
    @staticmethod
    def export(p50: float, p95: float, p99: float) -> str:
        return (
            f'amqp_publish_latency_ms{{quantile="0.5"}} {p50:.2f}\n'
            f'amqp_publish_latency_ms{{quantile="0.95"}} {p95:.2f}\n'
            f'amqp_publish_latency_ms{{quantile="0.99"}} {p99:.2f}\n'
        )
