# DEFECTIVE METRIC INSTRUMENTATION (PRE-INCIDENT)
PACKAGE_DELIVERY_HISTOGRAM.labels(
    depot_id="EU-NORTH-01",
    tracking_id=str(package.tracking_uuid),  # <--- CRITICAL FATAL DEFECT!
).observe(delivery_duration)
