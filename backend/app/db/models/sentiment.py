from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SentimentData(Base):
    __tablename__ = 'sentiment_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    legacy_score: Mapped[float | None] = mapped_column('score', Float, nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default='system')
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('ix_sentiment_data_symbol', 'symbol'),
        Index('ix_sentiment_data_symbol_timestamp', 'symbol', 'timestamp'),
    )
