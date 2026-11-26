# Constructing a hierarchical composite exception tree
network_errors = ExceptionGroup(
    "Network Cluster Failures",
    [
        ConnectionResetError("Socket reset by peer: redis-01"),
        TimeoutError("Connection timed out: postgres-read-replica"),
    ]
)

validation_errors = ExceptionGroup(
    "Payload Validation Failures",
    [
        ValueError("Field 'account_id' must be a valid UUIDv4"),
        KeyError("Missing mandatory metadata key 'tenant_id'"),
    ]
)

root_batch_error = ExceptionGroup(
    "Batch Pipeline Execution Failed",
    [network_errors, validation_errors, RuntimeError("Memory pressure threshold exceeded")]
)
