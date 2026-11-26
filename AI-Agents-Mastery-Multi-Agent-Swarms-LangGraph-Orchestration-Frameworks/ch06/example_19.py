class SwarmBackpressureGovernor:
    def __init__(self, high_watermark: int = 50, low_watermark: int = 10):
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self.is_paused = False

    def inspect_queue_depth(self, current_depth: int) -> bool:
        if current_depth >= self.high_watermark and not self.is_paused:
            self.is_paused = True
            print(f"[BACKPRESSURE ALERT] High watermark ({self.high_watermark}) reached! Pausing upstream producers.")
            return False # Signal to pause ingestion
        elif current_depth <= self.low_watermark and self.is_paused:
            self.is_paused = False
            print(f"[BACKPRESSURE RECOVERY] Low watermark ({self.low_watermark}) reached. Resuming ingestion.")
            return True
        return not self.is_paused
