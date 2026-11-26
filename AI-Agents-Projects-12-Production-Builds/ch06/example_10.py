from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def next_business_send_window(now_utc: datetime, prospect_tz: str, start_hour: int = 9, end_hour: int = 16) -> datetime:
    tz = ZoneInfo(prospect_tz)
    local_dt = now_utc.astimezone(tz)

    if local_dt.weekday() >= 5 or local_dt.hour >= end_hour:
        days_ahead = 1
        candidate = (local_dt + timedelta(days=days_ahead)).replace(hour=start_hour, minute=15, second=0, microsecond=0)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    if local_dt.hour < start_hour:
        candidate = local_dt.replace(hour=start_hour, minute=15, second=0, microsecond=0)
        return candidate.astimezone(timezone.utc)

    return now_utc


def domain_daily_quota(warmup_day: int, base_limit: int = 40, max_limit: int = 400) -> int:
    scaled = int(base_limit * (1.15 ** max(0, warmup_day - 1)))
    return min(max_limit, scaled)


if __name__ == "__main__":
    utc_now = datetime(2026, 11, 25, 22, 30, tzinfo=timezone.utc)
    scheduled = next_business_send_window(utc_now, "Europe/London")
    print("Scheduled UTC:", scheduled.isoformat())
    print("Warmup Day 10 Quota:", domain_daily_quota(10))
