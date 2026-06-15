from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelLog:
    ticker: str
    model_type: str = 'ml'
    is_active: bool = True
    trained_at: datetime | None = None