from datetime import datetime

from pydantic import BaseModel, Field


class ScheduleEventRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime


class ScheduleEventData(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    sync_status: str
    google_event_id: str
