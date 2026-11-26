# Recording an event internally within the aggregate
self._events.append(
    OrderSubmittedEvent(
        order_id=self.id,
        customer_id=self.customer_id,
        total_amount=self.total.amount,
        currency=self.currency.value,
        timestamp=datetime.now(timezone.utc),
    )
)
