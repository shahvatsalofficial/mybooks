# DISASTROUS CARDINALITY EXPLOSION ANTI-PATTERN
http_requests_total.labels(
    method="POST",
    endpoint="/checkout",
    user_id=str(user.id),  # <--- FATAL FLAW: 10,000,000 unique users!
)
