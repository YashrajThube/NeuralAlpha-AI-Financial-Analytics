from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = 'predictions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol: Mapped[str] = mapped_column(String(16), nullable=False)
    legacy_predicted_price: Mapped[float | None] = mapped_column('predicted_price', Float, nullable=True)
    prediction_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default='ml-v1')
    features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    legacy_timestamp: Mapped[datetime | None] = mapped_column('timestamp', DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user = relationship('User', back_populates='predictions', lazy='joined')

    __table_args__ = (
        Index('ix_predictions_symbol', 'symbol'),
        Index('ix_predictions_symbol_created_at', 'symbol', 'created_at'),
        Index('ix_predictions_user_created_at', 'user_id', 'created_at'),
    )
