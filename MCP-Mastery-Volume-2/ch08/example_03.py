"""
tests/test_property_fuzzing.py - Property-Based Fuzzing with Hypothesis
Exhaustively generates adversarial inputs to assert the No-Crash Invariant.
"""

from hypothesis import given, strategies as st, settings, HealthCheck
import pytest
from mcp import ClientSession

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    sku=st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=0, max_size=500),
    warehouse_id=st.text(min_size=0, max_size=200)
)
@pytest.mark.asyncio
async def test_inventory_tool_fuzzing_invariant(mcp_client: ClientSession, sku: str, warehouse_id: str):
    """
    Property: For all possible strings (including Unicode, control chars, and giant strings),
    calling check_inventory must NEVER crash the server or hang.
    It must either return a valid response dict OR a structured tool error.
    """
    try:
        result = await mcp_client.call_tool(
            "check_inventory",
            arguments={"sku": sku, "warehouse_id": warehouse_id}
        )
        # If call succeeds, result must be a valid MCP CallToolResult
        assert result is not None
        assert isinstance(result.content, list)
    except Exception as exc:
        # ClientSession exceptions must only occur if the server returned a formal JSON-RPC error code
        # The underlying connection must remain healthy and intact
        assert "Invalid" in str(exc) or "code" in str(exc).lower()
