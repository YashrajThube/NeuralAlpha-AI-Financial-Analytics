from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class FinancialData:
    id: UUID | int
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str | None = None
