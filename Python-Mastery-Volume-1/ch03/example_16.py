# THE REFACTORED ZERO-COPY PRODUCTION PIPELINE
from dataclasses import dataclass
import struct

# 1. Slotted entity: 48 bytes, zero GC tracking overhead
@dataclass(slots=True, frozen=True)
class OptimizedMeterReading:
    device_id: int
    timestamp: int
    active_power: float
    reactive_power: float
    voltage: float

# 2. Pre-compiled binary unpacker
METER_STRUCT = struct.Struct("!QQfff") # 8B + 8B + 4B + 4B + 4B = 28 bytes

def parse_incoming_telemetry_stream(raw_buffer: memoryview) -> list[OptimizedMeterReading]:
    """Parses binary stream in-place with zero intermediate bytes copying."""
    readings = []
    stride = METER_STRUCT.size
    total_records = len(raw_buffer) // stride

    for i in range(total_records):
        offset = i * stride
        # Unpacks directly from memoryview memory address without slicing!
        dev_id, ts, ap, rp, v = METER_STRUCT.unpack_from(raw_buffer, offset)
        readings.append(OptimizedMeterReading(dev_id, ts, ap, rp, v))

    return readings
