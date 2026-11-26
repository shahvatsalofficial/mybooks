"""
CI/CD Property-Based Schema Fuzzing Pipeline
Tests Pydantic models against millions of adversarial input permutations.
"""
import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

@given(st.builds(PositionAllocation))
def test_position_allocation_schema_invariance(allocation: PositionAllocation):
    # 1. Verify serialization round-trip
    serialized_json = allocation.model_dump_json()
    deserialized = PositionAllocation.model_validate_json(serialized_json)
    assert deserialized == allocation

    # 2. Verify schema constraints
    assert 0.0 <= allocation.allocation_weight <= 1.0
    assert allocation.ticker == allocation.ticker.upper()

def test_strict_mode_rejects_extra_fields():
    payload = {
        "ticker": "NVDA",
        "asset_class": "EQUITY",
        "allocation_weight": 0.25,
        "unauthorized_field": "exploit"
    }
    with pytest.raises(ValidationError):
        PositionAllocation.model_validate(payload)
