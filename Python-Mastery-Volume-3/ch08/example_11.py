# REMEDIATED LOW-CARDINALITY METRIC
PACKAGE_DELIVERY_HISTOGRAM.labels(
    depot_id="EU-NORTH-01",
    status="COMPLETED",  # Bounded enum (COMPLETED, FAILED, RETRIED)
).observe(delivery_duration)
