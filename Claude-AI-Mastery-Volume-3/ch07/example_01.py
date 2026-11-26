"""
production_bedrock_otel_tracer.py
Enterprise OpenTelemetry Instrumentation Gateway for Anthropic Claude on AWS Bedrock.
Complies with OpenTelemetry GenAI Semantic Conventions v1.28+ and W3C Tracecontext.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure structured enterprise logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EnterpriseBedrockTracer")

# Initialize global OpenTelemetry Tracer Provider
provider = TracerProvider()
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://otel-collector.observability.internal:4317", insecure=True),
    max_queue_size=2048,
    schedule_delay_millis=5000,
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("enterprise.claude.bedrock", "1.0.0")


class BedrockClaudeTelemetryGateway:
    """Production enterprise gateway executing Claude invocations with deep OTel instrumentation."""

    def __init__(
        self,
        region_name: str = "us-east-1",
        default_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        cost_center: str = "AI-CORE-FINANCE-01",
    ):
        self.region_name = region_name
        self.default_model_id = default_model_id
        self.cost_center = cost_center
        
        boto_config = Config(
            region_name=self.region_name,
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60,
        )
        self.bedrock_runtime = boto3.client("bedrock-runtime", config=boto_config)
        logger.info(
            "Initialized BedrockClaudeTelemetryGateway | Region: %s | Model: %s",
            self.region_name,
            self.default_model_id,
        )

    def invoke_model_instrumented(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        parent_traceparent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a synchronous Claude invocation with full OpenTelemetry span attribution.
        
        Args:
            messages: Anthropic conversation messages array.
            system_prompt: Optional system persona or prompt cache prefix.
            max_tokens: Maximum tokens for generation.
            temperature: Sampling temperature (0.0 for deterministic enterprise execution).
            parent_traceparent: Incoming W3C traceparent string from upstream API Gateway.
            session_id: Correlated enterprise conversational session UUID.
        
        Returns:
            Dictionary containing model text output, token breakdown, and trace metadata.
        """
        carrier = {}
        if parent_traceparent:
            carrier["traceparent"] = parent_traceparent
        
        extracted_context = TraceContextTextMapPropagator().extract(carrier=carrier)
        effective_session_id = session_id or str(uuid.uuid4())

        # Construct payload adhering to Bedrock Messages API specification
        body_payload: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            body_payload["system"] = system_prompt

        # Start OpenTelemetry Root/Child Span
        with tracer.start_as_current_span(
            name="claude.bedrock.invoke",
            context=extracted_context,
            kind=SpanKind.CLIENT,
        ) as span:
            # Inject mandatory GenAI Semantic Conventions
            span.set_attribute("gen_ai.system", "anthropic")
            span.set_attribute("gen_ai.request.model", self.default_model_id)
            span.set_attribute("gen_ai.request.temperature", temperature)
            span.set_attribute("gen_ai.request.max_tokens", max_tokens)
            span.set_attribute("enterprise.cost_center", self.cost_center)
            span.set_attribute("enterprise.session_id", effective_session_id)
            span.set_attribute("aws.region", self.region_name)

            start_time = time.perf_counter()
            try:
                logger.debug("Dispatching InvokeModel request to Bedrock...")
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.default_model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(body_payload),
                )
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                raw_body = response["body"].read().decode("utf-8")
                response_json = json.loads(raw_body)

                # Extract token usage and cache metrics
                usage = response_json.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                cache_read_tokens = usage.get("cache_read_input_tokens", 0)
                cache_creation_tokens = usage.get("cache_creation_input_tokens", 0)
                stop_reason = response_json.get("stop_reason", "end_turn")

                # Set span attributes for metrics aggregation
                span.set_attribute("gen_ai.usage.prompt_tokens", input_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", output_tokens)
                span.set_attribute("gen_ai.usage.cache_read_tokens", cache_read_tokens)
                span.set_attribute("gen_ai.usage.cache_creation_tokens", cache_creation_tokens)
                span.set_attribute("gen_ai.response.finish_reasons", [stop_reason])
                span.set_attribute("latency.total_ms", latency_ms)

                # Extract response text
                text_content = ""
                for block in response_json.get("content", []):
                    if block.get("type") == "text":
                        text_content += block.get("text", "")

                span.set_status(Status(StatusCode.OK))
                logger.info(
                    "Bedrock Invocation Completed | Latency: %.2fms | Tokens: In=%d, Out=%d, CacheHit=%d",
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                )

                return {
                    "text": text_content,
                    "model_id": self.default_model_id,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cache_read_tokens": cache_read_tokens,
                        "cache_creation_tokens": cache_creation_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    },
                    "latency_ms": latency_ms,
                    "trace_id": format(span.get_span_context().trace_id, "032x"),
                    "span_id": format(span.get_span_context().span_id, "016x"),
                }

            except ClientError as client_err:
                error_code = client_err.response.get("Error", {}).get("Code", "UnknownClientError")
                error_msg = client_err.response.get("Error", {}).get("Message", str(client_err))
                span.record_exception(client_err)
                span.set_status(Status(StatusCode.ERROR, f"{error_code}: {error_msg}"))
                span.set_attribute("error.type", error_code)
                logger.error("AWS Bedrock Client Error: %s — %s", error_code, error_msg)
                raise

            except Exception as ex:
                span.record_exception(ex)
                span.set_status(Status(StatusCode.ERROR, str(ex)))
                logger.error("Unexpected failure during Bedrock execution: %s", str(ex), exc_info=True)
                raise
