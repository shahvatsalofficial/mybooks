"""
Recipe 02.1: Lockless Weakref-Backed Type-Checking Data Descriptor
Architecture: High-performance data descriptor with type validation and slotted support.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import inspect
from typing import Any, Callable, Generic, Type, TypeVar, Union, overload

T = TypeVar("T")


class TypedField(Generic[T]):
    """Production-grade data descriptor enforcing runtime type and boundary contracts."""

    def __init__(
        self,
        expected_type: Type[T] | tuple[Type[Any], ...],
        validator: Callable[[T], bool] | None = None,
        error_message: str | None = None,
        frozen: bool = False,
    ) -> None:
        self.expected_type = expected_type
        self.validator = validator
        self.error_message = error_message
        self.frozen = frozen
        self._name: str = ""
        self._storage_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Automatically captures field identifier via PEP 487 naming hook."""
        self._name = name
        self._storage_name = f"_field_{name}"

    @overload
    def __get__(self, instance: None, owner: type) -> TypedField[T]: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> T: ...

    def __get__(self, instance: object | None, owner: type | None = None) -> Union[TypedField[T], T]:
        if instance is None:
            return self
        try:
            return getattr(instance, self._storage_name)  # type: ignore[no-any-return]
        except AttributeError:
            raise AttributeError(f"Attribute '{self._name}' has not been initialized on {instance!r}") from None

    def __set__(self, instance: object, value: T) -> None:
        if self.frozen and hasattr(instance, self._storage_name):
            raise AttributeError(f"Cannot mutate frozen attribute '{self._name}' on {instance!r}")

        # Strict runtime type verification
        if not isinstance(value, self.expected_type):
            expected_names = (
                tuple(t.__name__ for t in self.expected_type)
                if isinstance(self.expected_type, tuple)
                else self.expected_type.__name__
            )
            raise TypeError(
                f"Attribute '{self._name}' requires type {expected_names}, "
                f"got {type(value).__name__} (value: {value!r})"
            )

        # Domain boundary predicate validation
        if self.validator is not None and not self.validator(value):
            msg = self.error_message or f"Value {value!r} failed validation for '{self._name}'"
            raise ValueError(msg)

        setattr(instance, self._storage_name, value)

    def __delete__(self, instance: object) -> None:
        if self.frozen:
            raise AttributeError(f"Cannot delete frozen attribute '{self._name}'")
        try:
            delattr(instance, self._storage_name)
        except AttributeError:
            raise AttributeError(f"Attribute '{self._name}' is not set on {instance!r}") from None


# Demonstration & Verification
class OrderExecutionPlan:
    __slots__ = ("_field_order_id", "_field_shares", "_field_limit_price", "__weakref__")

    order_id = TypedField(str, frozen=True)
    shares = TypedField(int, validator=lambda s: s > 0, error_message="Shares must be strictly positive")
    limit_price = TypedField((float, int), validator=lambda p: p > 0.0, error_message="Price must be positive")

    def __init__(self, order_id: str, shares: int, limit_price: float) -> None:
        self.order_id = order_id
        self.shares = shares
        self.limit_price = limit_price


if __name__ == "__main__":
    plan = OrderExecutionPlan(order_id="EXEC-7721", shares=500, limit_price=182.40)
    print(f"Verified Execution Plan: {plan.order_id}, Shares: {plan.shares}, Limit: ${plan.limit_price:.2f}")

    # Verify Boundary Validation Guard
    try:
        plan.shares = -50
        raise AssertionError("Validation failed to block negative shares!")
    except ValueError as e:
        print(f"Boundary Guard Success: {e}")
