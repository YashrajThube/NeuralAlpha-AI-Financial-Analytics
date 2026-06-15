from app.db.base import Base
from app.db.models.logs import LogEntry
from app.db.models.market_data import MarketData
from app.db.models.portfolio import Portfolio
from app.db.models.prediction import Prediction
from app.db.models.scheduled_event import ScheduledEvent
from app.db.models.sentiment import SentimentData
from app.db.models.user import User
from app.db.session import engine


async def init_db() -> None:
    _ = User, Prediction, MarketData, SentimentData, Portfolio, LogEntry, ScheduledEvent
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
