from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class ColumnSpec(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_partition_key: bool = False
    is_pii: bool = False
    description: str = ""
    sample_values: List[str] = Field(default_factory=list)


class ForeignKeyEdge(BaseModel):
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    cardinality: str = "many_to_one"


class TableSpec(BaseModel):
    schema_name: str = "analytics"
    table_name: str
    row_count_estimate: int = 0
    size_bytes: int = 0
    description: str = ""
    columns: List[ColumnSpec] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyEdge] = Field(default_factory=list)

    @property
    def fqn(self) -> str:
        return f"{self.schema_name}.{self.table_name}"

    def to_compact_ddl(self, mask_pii: bool = True) -> str:
        lines = [
            f"-- Table: {self.fqn} (~{self.row_count_estimate:,} rows) | {self.description}"
        ]
        for col in self.columns:
            if mask_pii and col.is_pii:
                lines.append(f"  {col.name} {col.data_type} [REDACTED_PII]")
                continue
            flags: List[str] = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_partition_key:
                flags.append("PARTITION_KEY")
            if not col.is_nullable:
                flags.append("NOT NULL")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            samples = (
                f" e.g. {col.sample_values[:3]}" if col.sample_values else ""
            )
            lines.append(f"  {col.name} {col.data_type}{flag_str}{samples}")
        return "\n".join(lines)


class CatalogSnapshot(BaseModel):
    captured_at: float
    dialect: str = "postgres"
    tables: Dict[str, TableSpec] = Field(default_factory=dict)


class LiveCatalogIntrospector:
    """Async schema introspector with TTL caching and metadata enrichment."""

    def __init__(self, ttl_seconds: int = 300, dialect: str = "postgres") -> None:
        self.ttl_seconds = ttl_seconds
        self.dialect = dialect
        self._cache: Optional[CatalogSnapshot] = None
        self._lock = asyncio.Lock()

    async def _fetch_raw_metadata(self) -> Dict[str, TableSpec]:
        await asyncio.sleep(0.015)
        merchants = TableSpec(
            table_name="merchants", row_count_estimate=420_000, size_bytes=94_000_000,
            description="Registered merchant accounts and risk tiers.",
            columns=[
                ColumnSpec(name="id", data_type="BIGINT", is_nullable=False, is_primary_key=True),
                ColumnSpec(name="merchant_name", data_type="TEXT", is_nullable=False),
                ColumnSpec(name="category_id", data_type="INT", is_nullable=False),
                ColumnSpec(name="country_code", data_type="CHAR(2)", sample_values=["US", "IN", "GB"]),
                ColumnSpec(name="tax_id", data_type="TEXT", is_pii=True),
            ],
            foreign_keys=[ForeignKeyEdge(source_table="analytics.merchants", source_column="category_id", target_table="analytics.merchant_categories", target_column="id")],
        )
        categories = TableSpec(
            table_name="merchant_categories", row_count_estimate=180, size_bytes=48_000,
            description="MCC lookup table for merchant industry verticals.",
            columns=[
                ColumnSpec(name="id", data_type="INT", is_nullable=False, is_primary_key=True),
                ColumnSpec(name="mcc_code", data_type="VARCHAR(4)", is_nullable=False),
                ColumnSpec(name="category_name", data_type="TEXT", sample_values=["SaaS", "Retail", "Travel"]),
            ],
        )
        settlements = TableSpec(
            table_name="settlement_events", row_count_estimate=4_200_000_000, size_bytes=1_850_000_000_000,
            description="Partitioned card settlement ledger events.",
            columns=[
                ColumnSpec(name="event_id", data_type="UUID", is_nullable=False, is_primary_key=True),
                ColumnSpec(name="merchant_id", data_type="BIGINT", is_nullable=False),
                ColumnSpec(name="settled_date", data_type="DATE", is_nullable=False, is_partition_key=True),
                ColumnSpec(name="amount_cents", data_type="BIGINT", is_nullable=False),
                ColumnSpec(name="status", data_type="VARCHAR(24)", sample_values=["settled", "failed", "pending"]),
            ],
            foreign_keys=[ForeignKeyEdge(source_table="analytics.settlement_events", source_column="merchant_id", target_table="analytics.merchants", target_column="id")],
        )
        return {t.fqn: t for t in (merchants, categories, settlements)}

    async def get_snapshot(self, force_refresh: bool = False) -> CatalogSnapshot:
        async with self._lock:
            now = time.monotonic()
            if (
                not force_refresh
                and self._cache is not None
                and (now - self._cache.captured_at) < self.ttl_seconds
            ):
                return self._cache
            tables = await self._fetch_raw_metadata()
            self._cache = CatalogSnapshot(
                captured_at=now, dialect=self.dialect, tables=tables
            )
            return self._cache


async def demo_introspection() -> None:
    introspector = LiveCatalogIntrospector(ttl_seconds=300)
    t0 = time.perf_counter()
    snap1 = await introspector.get_snapshot()
    t1 = time.perf_counter()
    snap2 = await introspector.get_snapshot()
    t2 = time.perf_counter()
    print(f"Tables loaded: {len(snap1.tables)} | Cold fetch: {(t1 - t0)*1000:.2f} ms | Cached fetch: {(t2 - t1)*1000:.2f} ms")
    print(snap2.tables["analytics.settlement_events"].to_compact_ddl())


if __name__ == "__main__":
    asyncio.run(demo_introspection())
