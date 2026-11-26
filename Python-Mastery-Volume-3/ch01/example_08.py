# infrastructure/anti_corruption_layer.py
"""Anti-Corruption Layer (ACL) translating external vendor schemas into domain Value Objects."""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from domain.model import Currency, Money, SkuId
from domain.exceptions import DomainValidationError


class ExternalBillingProviderACL:
    """Insulates the billing domain core from volatile third-party payment gateway payloads."""

    @staticmethod
    def to_domain_money(payload: dict[str, Any]) -> Money:
        """Translates external payment provider JSON payload into an immutable Money Value Object."""
        try:
            raw_amount = payload.get("charge_amount_cents")
            if raw_amount is None:
                raise DomainValidationError("Payment gateway payload missing 'charge_amount_cents'.")

            # Convert integer cents from vendor gateway to Decimal standard currency units
            decimal_amount = Decimal(raw_amount) / Decimal("100")

            raw_currency = payload.get("currency_iso", "").upper()
            try:
                currency = Currency[raw_currency]
            except KeyError:
                raise DomainValidationError(f"Unsupported gateway currency code: '{raw_currency}'")

            return Money(amount=decimal_amount, currency=currency)

        except (InvalidOperation, TypeError) as err:
            raise DomainValidationError(f"Invalid monetary numeric format from gateway: {err}") from err
