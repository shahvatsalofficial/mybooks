class SlottedTelemetryReading:
    __slots__ = ("sensor_id", "timestamp", "value")

    def __init__(self, sensor_id: int, timestamp: int, value: float) -> None:
        self.sensor_id = sensor_id
        self.timestamp = timestamp
        self.value = value
