# tests/test_financial_properties.py
"""Property-based invariant testing for financial ledger calculations using Hypothesis."""

from __future__ import annotations
from decimal import Decimal
import pytest
from hypothesis import given, settings, strategies as st

from domain.model import Currency, Money, OrderAggregate, SkuId


# Custom Hypothesis strategy generating realistic Decimal currency amounts
st_currency = st.sampled_from([Currency.USD, Currency.EUR, Currency.GBP])
st_cents = st.integers(min_value=1, max_value=10_000_000)  # $0.01 to $100,000.00
st_money = st.builds(
    lambda cents, curr: Money(Decimal(cents) / Decimal("100"), curr),
    cents=st_cents,
    curr=st_currency,
)


@given(
    amount_a=st_cents,
    amount_b=st_cents,
    currency=st_currency,
)
@settings(max_examples=500)
def test_money_addition_commutativity_property(amount_a: int, amount_b: int, currency: Currency) -> None:
    """Mathematical Invariant: Money addition MUST be strictly commutative (a + b == b + a)."""
    m1 = Money(Decimal(amount_a) / Decimal("100"), currency)
    m2 = Money(Decimal(amount_b) / Decimal("100"), currency)

    res1 = m1 + m2
    res2 = m2 + m1

    assert res1 == res2, f"Commutativity failed: {m1} + {m2} != {m2} + {m1}"
    assert res1.currency == currency


@given(
    allocations=st.lists(st_cents, min_size=1, max_size=50),
    currency=st_currency,
)
@settings(max_examples=500)
def test_financial_conservation_of_funds_property(allocations: list[int], currency: Currency) -> None:
    """Conservation of Funds Invariant: Sum of partitioned allocations must exactly equal total balance.
    
    Zero pennies may ever be created or destroyed due to rounding errors.
    """
    total_cents = sum(allocations)
    total_money = Money(Decimal(total_cents) / Decimal("100"), currency)

    # Partition total into individual money value objects
    partitioned_parts = [Money(Decimal(c) / Decimal("100"), currency) for c in allocations]

    accumulated = Money(Decimal("0.00"), currency)
    for part in partitioned_parts:
        accumulated += part

    assert accumulated == total_money, (
        f"Conservation of funds violated! Expected {total_money}, got {accumulated}"
    )
