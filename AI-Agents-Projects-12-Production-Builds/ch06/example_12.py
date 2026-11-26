from __future__ import annotations

import asyncio
from dataclasses import dataclass, field


@dataclass
class MockCrmStore:
    records: dict[str, dict[str, object]] = field(default_factory=dict)

    async def upsert_with_cas(self, record_id: str, expected_version: int, patch: dict[str, object]) -> tuple[bool, int]:
        await asyncio.sleep(0.01)
        row = self.records.get(record_id)
        if row is None:
            self.records[record_id] = {**patch, "version": 1}
            return True, 1
        current_ver = int(row["version"])
        if current_ver != expected_version:
            return False, current_ver
        row.update(patch)
        row["version"] = current_ver + 1
        return True, int(row["version"])


async def main() -> None:
    store = MockCrmStore(records={"OPP-90211": {"meddic_score": 72, "version": 3}})
    ok_stale, server_ver = await store.upsert_with_cas("OPP-90211", expected_version=2, patch={"meddic_score": 89})
    print(f"Stale CAS attempt: ok={ok_stale} server_version={server_ver}")

    ok_fresh, new_ver = await store.upsert_with_cas("OPP-90211", expected_version=server_ver, patch={"meddic_score": 89})
    print(f"Fresh CAS attempt: ok={ok_fresh} new_version={new_ver}")


if __name__ == "__main__":
    asyncio.run(main())
