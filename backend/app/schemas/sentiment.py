from datetime import datetime

from pydantic import BaseModel


class SentimentDataResponse(BaseModel):
    symbol: str
    score: float
    label: str
    timestamp: datetime
