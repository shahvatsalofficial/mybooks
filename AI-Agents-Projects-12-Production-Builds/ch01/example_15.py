from __future__ import annotations

import hashlib
import json
import tempfile
import time
from pathlib import Path


class DiskQueryCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, query: str, tier: str) -> Path:
        digest = hashlib.sha256(f"{query}::{tier}".encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{digest}.json"

    def get(self, query: str, tier: str) -> dict | None:
        path = self._key_path(query, tier)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - payload["cached_at"] > self.ttl_seconds:
            path.unlink(missing_ok=True)
            return None
        return payload["data"]

    def put(self, query: str, tier: str, data: dict) -> Path:
        path = self._key_path(query, tier)
        envelope = {"cached_at": time.time(), "data": data}
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return path


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        cache = DiskQueryCache(Path(tmp), ttl_seconds=60)
        p = cache.put("FIPS 203 ML-KEM", "primary_official", {"hits": 4, "top_url": "https://csrc.nist.gov"})
        hit = cache.get("FIPS 203 ML-KEM", "primary_official")
        miss = cache.get("unknown query", "primary_official")
        print(f"Cache file={p.name} hit_keys={list(hit.keys()) if hit else None} miss={miss}")
