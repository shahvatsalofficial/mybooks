"""
tests/test_inventory_tools.py - Unit Tests for MCP Inventory Tools
"""

import pytest
from mcp import ClientSession
from mcp.types import TextContent

@pytest.mark.asyncio
async def test_check_inventory_success(mcp_client: ClientSession):
    """Verify check_inventory succeeds with valid SKU and warehouse parameters."""
    result = await mcp_client.call_tool(
        "check_inventory",
        arguments={"sku": "SKU-9921", "warehouse_id": "WH-NORTH"}
    )

    assert result is not None
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    
    # Parse structured JSON payload returned by tool
    import json
    data = json.loads(result.content[0].text)
    assert data["sku"] == "SKU-9921"
    assert data["warehouse_id"] == "WH-NORTH"
    assert data["available_units"] == 142
    assert data["status"] == "IN_STOCK"


@pytest.mark.asyncio
async def test_check_inventory_invalid_sku_boundary(mcp_client: ClientSession):
    """Verify tool catches invalid SKU format and returns clean error message."""
    result = await mcp_client.call_tool(
        "check_inventory",
        arguments={"sku": "INVALID-FORMAT", "warehouse_id": "WH-NORTH"}
    )
    
    # FastMCP catches internal ValueErrors and reports tool execution failure
    assert result.isError is True
    assert len(result.content) == 1
    assert "Invalid SKU format" in result.content[0].text


@pytest.mark.asyncio
async def test_warehouse_metrics_resource_read(mcp_client: ClientSession):
    """Verify dynamic resource URI resolution and text content retrieval."""
    resource_uri = "inventory://metrics/WH-NORTH"
    resource_data = await mcp_client.read_resource(resource_uri)

    assert resource_data is not None
    assert len(resource_data.contents) == 1
    content = resource_data.contents[0]
    assert content.uri == resource_uri
    assert "Status: OPERATIONAL" in content.text
    assert "Capacity: 88%" in content.text


### 8.2.4 Deterministic Mocking of Third-Party Dependencies in Async Lifespans

A frequent dilemma in unit testing MCP servers is how to isolate tool handlers from physical external infrastructure (such as PostgreSQL relational clusters, Redis caches, AWS S3 buckets, or external SaaS REST APIs) without introducing brittle monkey-patching. If an in-memory test attempts to connect to a live database or cloud service, tests become slow, flaky, prone to network partition failures, and unexecutable in air-gapped CI environments.

The recommended architectural pattern utilizes **Dependency Injection via Server Lifespans and Fixtures**:

1. **Protocol Lifespan Context**: When an MCP server initializes, its startup lifecycle context yields an application state dictionary or typed dependency container. In production, this container holds live connection pools and authenticated cloud clients. In test environments, the test fixture overrides these dependencies with deterministic in-memory doubles (such as an in-memory SQLite database via SQLAlchemy, `fakeredis`, or `moto` for mock AWS services).
2. **Deterministic Time and Clock Mocking**: Tools that perform time-windowed rate limiting, token expiration checks, or telemetry event generation must avoid querying `datetime.now()` or `time.time()` directly. Injecting an abstract clock interface or using libraries like `time-machine` allows test cases to advance time deterministically, asserting that resource caches expire precisely after their designated Time-To-Live (TTL) without calling `asyncio.sleep()`.
3. **Simulating Downstream Flakiness and Circuit Breaking**: Real-world cloud dependencies fail probabilistically. Unit test suites should intentionally configure mock clients to simulate HTTP 503 Service Unavailable, connection resets, and socket timeouts. Asserting that tool handlers catch downstream network errors, gracefully engage internal circuit breakers, and return informative error messages prevents agent tool-calling loops from cascading into catastrophic system halts.

### 8.2.5 Golden Master Schema Snapshot Verification

Because LLM agents generate tool calls strictly based on the JSON Schema exposed during `tools/list`, any unintentional mutation of the schema constitutes a breaking API change. For example, renaming a parameter from `warehouse_id` to `warehouse` or changing a parameter description string can degrade an agent's tool-selection accuracy from 98% to 65%.

To prevent schema regressions, enterprise teams implement **Golden Master Schema Snapshot Testing**:
- When a tool is initially approved and certified, its emitted JSON Schema is serialized to a canonical JSON file in the test repository (e.g., `tests/snapshots/inventory_tools.schema.json`).
- During every CI test run, the test harness calls `mcp_client.list_tools()`, extracts the generated JSON Schema for all tools, sorts object keys canonically, and asserts exact character-for-character equality against the committed golden snapshot.
- Any intentional schema update requires an explicit review and update of the golden snapshot file, ensuring that API surface changes are never introduced accidentally during refactoring.

---

## 8.3 JSON-RPC 2.0 Protocol Conformance & Boundary Fuzzing

While unit tests verify high-level application logic, they assume that incoming requests are well-formed and conform perfectly to high-level SDK interfaces. However, in production, MCP servers receive raw serialized strings over standard input or HTTP POST endpoints. Host processes can terminate unexpectedly, network proxies can truncate frames, and malicious actors or compromised clients can inject malformed JSON-RPC structures.

Tier 2 testing subjects the server to strict **Protocol Conformance and Fuzzing**.

<div class="diagram-container">
<!-- Inlined: diag_ch08_protocol_conformance.svg -->
<img src="../assets/svg/diag_ch08_protocol_conformance.svg" alt="Automated Protocol Conformance & Schema Validation Engine" />
</div>

### 8.3.1 JSON-RPC 2.0 Specification Compliance Rules

According to the official Model Context Protocol specification and the underlying JSON-RPC 2.0 specification (RFC 8259), every compliant MCP server must adhere to the following invariants:
1. **Valid JSON-RPC Envelope**: Every request must be a valid JSON object containing `"jsonrpc": "2.0"`, a string `"method"`, and an optional `"id"` (string or integer) and `"params"` (object or array).
2. **Standard Error Code Integrity**: When errors occur, the server must return standard JSON-RPC 2.0 error codes:
   - `-32700` (**Parse Error**): Invalid JSON syntax received by the server.
   - `-32600` (**Invalid Request**): The JSON sent is not a valid JSON-RPC 2.0 request object.
   - `-32601` (**Method Not Found**): The requested method does not exist or is not available.
   - `-32602` (**Invalid Params**): The parameters provided do not match the declared schema or parameter structure.
   - `-32603` (**Internal Error**): An unhandled internal runtime error occurred.
   - `-32000 to -32099` (**Server Error**): Reserved for implementation-defined server errors.
3. **Strict Notification Semantics**: Requests without an `"id"` member are formal JSON-RPC Notifications. Compliant servers must execute notifications asynchronously and **never** send a response payload back to the client. Sending a response to a notification constitutes a fatal protocol violation.
4. **Idempotent Handshake Initialization**: The `initialize` method must be the first request processed. Any subsequent tool or resource invocation attempted prior to successful initialization must be rejected with `-32600` or `-32002` (Initialization Required).

### 8.3.2 Automated Conformance Fuzzer Implementation

The following test module implements an automated protocol fuzzing harness that sends raw, malformed, and adversarial JSON-RPC payloads over standard subprocess stdio streams, asserting strict protocol compliance and proper error handling.
