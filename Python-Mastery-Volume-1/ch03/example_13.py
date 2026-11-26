"""
Recipe 03.2: Ultra-Low-Latency Order Book with Bisect & Deque
File: recipe_03_2_order_book.py
Python Version: 3.12+
"""

from __future__ import annotations
import bisect
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(slots=True)
class Order:
    order_id: int
    price: float
    quantity: int
    timestamp_ns: int


class PriceLevel:
    __slots__ = ("price", "orders", "total_volume")

    def __init__(self, price: float) -> None:
        self.price = price
        self.orders: deque[Order] = deque()  # FIFO queue for price-time priority
        self.total_volume = 0

    def add_order(self, order: Order) -> None:
        self.orders.append(order)
        self.total_volume += order.quantity

    def execute_match(self, requested_qty: int) -> int:
        """Fills orders against this price level in strict FIFO order."""
        filled_qty = 0

        while self.orders and filled_qty < requested_qty:
            front_order = self.orders[0]
            remaining_needed = requested_qty - filled_qty

            if front_order.quantity <= remaining_needed:
                filled_qty += front_order.quantity
                self.total_volume -= front_order.quantity
                self.orders.popleft()  # O(1) eviction
            else:
                front_order.quantity -= remaining_needed
                self.total_volume -= remaining_needed
                filled_qty += remaining_needed

        return filled_qty


class HighPerformanceOrderBook:
    """L2 Limit Order Book using bisect-managed sorted arrays and chunked FIFO deques."""

    def __init__(self) -> None:
        self._bids: List[float] = []  # Sorted ascending
        self._asks: List[float] = []  # Sorted ascending
        self._bid_levels: Dict[float, PriceLevel] = {}
        self._ask_levels: Dict[float, PriceLevel] = {}

    def insert_order(self, order_id: int, side: str, price: float, quantity: int) -> None:
        """Inserts an order in O(log N) search time."""
        order = Order(order_id, price, quantity, time.perf_counter_ns())

        if side == "BUY":
            prices = self._bids
            levels = self._bid_levels
        else:
            prices = self._asks
            levels = self._ask_levels

        if price not in levels:
            # Binary bisection insertion maintains sorted invariant
            idx = bisect.bisect_left(prices, price)
            prices.insert(idx, price)
            levels[price] = PriceLevel(price)

        levels[price].add_order(order)

    def get_best_bid(self) -> Optional[float]:
        return self._bids[-1] if self._bids else None

    def get_best_ask(self) -> Optional[float]:
        return self._asks[0] if self._asks else None

    def match_market_order(self, side: str, quantity: int) -> int:
        """Executes a market order against opposing price levels."""
        unfilled = quantity

        if side == "BUY":
            # Buy matches against lowest Ask
            while self._asks and unfilled > 0:
                best_ask = self._asks[0]
                level = self._ask_levels[best_ask]
                filled = level.execute_match(unfilled)
                unfilled -= filled

                if level.total_volume == 0:
                    del self._ask_levels[best_ask]
                    self._asks.pop(0)  # Remove cleared price level
        else:
            # Sell matches against highest Bid
            while self._bids and unfilled > 0:
                best_bid = self._bids[-1]
                level = self._bid_levels[best_bid]
                filled = level.execute_match(unfilled)
                unfilled -= filled

                if level.total_volume == 0:
                    del self._bid_levels[best_bid]
                    self._bids.pop()  # O(1) pop from end

        return quantity - unfilled


# Verification Driver
if __name__ == "__main__":
    book = HighPerformanceOrderBook()

    # Seed order book with 10,000 orders
    start = time.perf_counter()
    for i in range(10_000):
        book.insert_order(i, "BUY", 180.0 + (i % 50) * 0.1, 10)
        book.insert_order(i + 10000, "SELL", 185.0 + (i % 50) * 0.1, 10)
    elapsed = time.perf_counter() - start

    print(f"[*] Ingested 20,000 orders into Book in {elapsed * 1000:.2f} ms")
    print(f"[*] Best Bid: ${book.get_best_bid():.2f} | Best Ask: ${book.get_best_ask():.2f}")

    # Execute market order match
    filled = book.match_market_order("BUY", 150)
    print(f"[*] Market Order Filled: {filled} units | New Best Ask: ${book.get_best_ask():.2f}")
