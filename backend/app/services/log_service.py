from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.logs import LogEntry


class LogService:
    @staticmethod
    async def create_log(
        db: AsyncSession,
        action: str,
        status: str,
        message: str | None = None,
        user_id: int | None = None,
    ) -> LogEntry:
        entry = LogEntry(
            user_id=user_id,
            action=action,
            status=status,
            message=message,
        )
        add = getattr(db, 'add', None)
        if callable(add):
            add(entry)
        flush = getattr(db, 'flush', None)
        if callable(flush):
            await flush()
        return entry
