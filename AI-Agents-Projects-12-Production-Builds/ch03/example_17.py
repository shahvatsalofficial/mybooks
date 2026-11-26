from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

def check_at_risk(elapsed_minutes: int, sla_minutes: int = 15) -> bool:
    remaining = sla_minutes - elapsed_minutes
    return remaining <= (sla_minutes * 0.25)

for mins in (5, 10, 12, 14):
    print(f"Elapsed {mins}m -> at_risk={check_at_risk(mins)}")
