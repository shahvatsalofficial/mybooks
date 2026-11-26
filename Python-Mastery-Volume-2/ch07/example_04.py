"""
Recipe 07.2: Apache Arrow IPC Streaming Buffer for In-Memory Transfer
Architecture: Zero-copy columnar IPC sharing using PyArrow buffer streams.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import io
import time
import pyarrow as pa
from typing import Tuple


class ArrowIPCChannel:
    """Manages zero-copy columnar serialization and zero-copy reader streams."""

    @staticmethod
    def create_sample_batch(row_count: int = 1_000_000) -> pa.RecordBatch:
        """Constructs an Arrow RecordBatch with contiguous numerical and string columns."""
        ids = pa.array(range(row_count), type=pa.int64())
        metrics = pa.array([x * 0.125 for x in range(row_count)], type=pa.float64())
        categories = pa.array(["EQUITY_TICK" if x % 2 == 0 else "OPTION_TICK" for x in range(row_count)])

        schema = pa.schema([
            pa.field("transaction_id", pa.int64()),
            pa.field("metric_value", pa.float64()),
            pa.field("category", pa.string()),
        ])

        return pa.RecordBatch.from_arrays([ids, metrics, categories], schema=schema)

    @classmethod
    def serialize_to_buffer(cls, batch: pa.RecordBatch) -> pa.Buffer:
        """Serializes RecordBatch into an Arrow IPC stream buffer with minimal overhead."""
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, batch.schema) as writer:
            writer.write_batch(batch)
        return sink.getvalue()

    @classmethod
    def read_zero_copy_from_buffer(cls, buffer: pa.Buffer) -> pa.Table:
        """Reads Arrow Table directly from buffer memory without memory duplication."""
        reader = pa.ipc.open_stream(buffer)
        table = reader.read_all()
        return table


# Demonstration & Verification
if __name__ == "__main__":
    rows = 2_000_000
    print(f"Generating {rows:,} row Arrow RecordBatch...")

    batch = ArrowIPCChannel.create_sample_batch(rows)
    print(f"RecordBatch Size in Memory: {batch.nbytes / (1024*1024):.2f} MB")

    # Serialize to Arrow IPC Buffer
    start_ser = time.perf_counter()
    arrow_buffer = ArrowIPCChannel.serialize_to_buffer(batch)
    ser_duration = time.perf_counter() - start_ser
    print(f"Serialized to IPC Buffer:   {len(arrow_buffer) / (1024*1024):.2f} MB in {ser_duration:.4f} s")

    # Zero-Copy Read
    start_read = time.perf_counter()
    unpacked_table = ArrowIPCChannel.read_zero_copy_from_buffer(arrow_buffer)
    read_duration = time.perf_counter() - start_read
    print(f"Zero-Copy Unpack Completed:  {unpacked_table.num_rows:,} rows in {read_duration:.4f} s")

    throughput_gb = (batch.nbytes / (1024**3)) / read_duration if read_duration > 0 else 0.0
    print(f"Unpack Bandwidth Throughput: {throughput_gb:.2f} GB/sec (Zero-Copy Bus Speed)")
    assert unpacked_table.num_rows == rows
