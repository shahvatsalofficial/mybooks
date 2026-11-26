# THE DEFECTIVE INGESTION PIPELINE
class MeterReading:
    # FLAW 1: Missing __slots__. Allocates full __dict__ per message
    def __init__(self, device_id, timestamp, active_power, reactive_power, voltage):
        self.device_id = device_id
        self.timestamp = timestamp
        self.active_power = active_power
        self.reactive_power = reactive_power
        self.voltage = voltage

class TelemetryIngestor:
    def __init__(self):
        # FLAW 2: Ingestion queue uses standard list. Slicing creates full buffer copies
        self.buffer = []

    def handle_raw_chunk(self, raw_socket_bytes):
        # FLAW 3: Substring slicing creates millions of transient string allocations
        header = raw_socket_bytes[0:16]
        data = raw_socket_bytes[16:]
        # Unpacks into unslotted MeterReading objects
        self.buffer.append(MeterReading(...))
