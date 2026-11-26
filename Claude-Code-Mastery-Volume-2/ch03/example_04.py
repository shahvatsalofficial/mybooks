from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class DateRangeQuery(BaseModel):
    start_time: datetime = Field(..., description="ISO 8601 start timestamp")
    end_time: datetime = Field(..., description="ISO 8601 end timestamp")
    
    @model_validator(mode="after")
    def verify_time_order(self) -> 'DateRangeQuery':
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly greater than start_time")
        duration = (self.end_time - self.start_time).total_seconds()
        if duration > 86400 * 30: # 30 days max
            raise ValueError("Query window cannot exceed 30 days")
        return self
