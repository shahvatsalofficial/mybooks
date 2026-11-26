# Without PEP 681 support:
class OrderRecord(BaseModel):
    order_id: str
    amount: float

# Mypy error in legacy checkers:
# error: Unexpected keyword argument "order_id" for "OrderRecord"
order = OrderRecord(order_id="ORD-991", amount=45.50)
