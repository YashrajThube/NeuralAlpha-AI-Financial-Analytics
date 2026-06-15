from __future__ import annotations

import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.scheduled_event import ScheduledEvent
from app.db.models.user import User
from app.schemas.scheduling import ScheduleEventData, ScheduleEventRequest
from app.services.calendar_service import CalendarService
from app.services.log_service import LogService


class SchedulingService:
    @staticmethod
    async def create_event(payload: ScheduleEventRequest, current_user: User, db: AsyncSession) -> ScheduleEventData:
        event = ScheduledEvent(
            user_id=current_user.id,
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
            sync_status='pending',
        )
        db.add(event)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()

        # Create then sync immediately to keep scheduling flow consistent.
        google_event_id = await CalendarService.create_event(payload.title, payload.start_time, payload.end_time)
        google_event_id = await CalendarService.sync_event(payload.title, payload.start_time, payload.end_time)
        event.google_event_id = google_event_id
        event.sync_status = 'synced'

        await LogService.create_log(
            db,
            user_id=current_user.id,
            action='calendar.sync',
            status='success',
            message=json.dumps({'event_id': event.id, 'google_event_id': google_event_id}),
        )

        return ScheduleEventData(
            id=event.id,
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            sync_status=event.sync_status,
            google_event_id=event.google_event_id or '',
        )

    @staticmethod
    async def list_events(current_user: User, db: AsyncSession) -> list[ScheduleEventData]:
        rows = await db.execute(
            select(ScheduledEvent)
            .where(ScheduledEvent.user_id == current_user.id)
            .order_by(ScheduledEvent.start_time.desc())
            .limit(50)
        )
        events = rows.scalars().all()
        return [
            ScheduleEventData(
                id=row.id,
                title=row.title,
                start_time=row.start_time,
                end_time=row.end_time,
                sync_status=row.sync_status,
                google_event_id=row.google_event_id or '',
            )
            for row in events
        ]
