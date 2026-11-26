"""
Recipe 08.2: OpenTelemetry Native Execution Span & Overhead Propagator
Architecture: Low-overhead OpenTelemetry SDK with BatchSpanProcessor and gRPC export.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import contextlib
import time
from typing import Any, Dict, Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource


class ProductionTelemetryManager:
    """Configures high-throughput, low-overhead OpenTelemetry tracing."""

    def __init__(self, service_name: str = "OrderExecutionService") -> None:
        self.service_name = service_name
        self._provider: TracerProvider | None = None
        self._tracer: trace.Tracer | None = None

    def initialize(self) -> trace.Tracer:
        """Initializes TracerProvider with bounded ring buffer (BatchSpanProcessor)."""
        resource = Resource.create({"service.name": self.service_name, "environment": "production"})
        self._provider = TracerProvider(resource=resource)

        # In production, replace ConsoleSpanExporter with OTLPSpanExporter (gRPC)
        exporter = ConsoleSpanExporter()

        # BatchSpanProcessor offloads span serialization to background worker thread:
        span_processor = BatchSpanProcessor(
            exporter,
            max_queue_size=8192,           # Max spans queued before dropping
            schedule_delay_millis=500,     # Export batch interval
            max_export_batch_size=512,     # Batch size per network flush
        )
        self._provider.add_span_processor(span_processor)
        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(self.service_name)
        return self._tracer

    @contextlib.contextmanager
    def trace_operation(self, operation_name: str, attributes: Dict[str, Any] | None = None) -> Generator[trace.Span, None, None]:
        """Low-overhead context manager tracking function execution duration."""
        if self._tracer is None:
            self.initialize()
            assert self._tracer is not None

        with self._tracer.start_as_current_span(operation_name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, v)
            yield span

    def shutdown(self) -> None:
        """Flushes in-memory span queue and cleanly terminates exporters."""
        if self._provider:
            self._provider.shutdown()


# Demonstration & Verification
if __name__ == "__main__":
    telemetry = ProductionTelemetryManager()
    tracer = telemetry.initialize()

    def execute_trade_transaction(symbol: str, shares: int, price: float) -> bool:
        with telemetry.trace_operation("execute_trade", {"symbol": symbol, "shares": shares}) as span:
            # Simulated trading latency
            time.sleep(0.01)
            span.set_attribute("execution.status", "FILLED")
            span.set_attribute("execution.fill_price", price)
            return True

    print("Executing traced transaction...")
    success = execute_trade_transaction("NVDA", 100, 142.50)
    print(f"Transaction Result: {success}")
    telemetry.shutdown()
    print("Telemetry shutdown completed cleanly.")
