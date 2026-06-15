from __future__ import annotations

import os
from datetime import datetime
from uuid import uuid4


class CalendarService:
    @staticmethod
    async def create_event(title: str, start_time: datetime, end_time: datetime) -> str:
        _ = title, start_time, end_time
        return f'evt-{uuid4().hex[:18]}'

    @staticmethod
    async def sync_event(title: str, start_time: datetime, end_time: datetime) -> str:
        _ = title, start_time, end_time

        # In production this can call Google Calendar APIs using OAuth credentials.
        has_calendar_credentials = bool(
            os.getenv('GOOGLE_CALENDAR_CLIENT_ID')
            and os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET')
            and os.getenv('GOOGLE_CALENDAR_REFRESH_TOKEN')
        )

        prefix = 'gcal' if has_calendar_credentials else 'local'
        return f'{prefix}-{uuid4().hex[:18]}'
