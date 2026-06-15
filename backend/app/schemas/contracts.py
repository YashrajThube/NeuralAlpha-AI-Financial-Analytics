from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class PredictionContractResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    predicted_value: float
    confidence_score: float
    model_type: str
    model_version: str = 'v1'
    ticker: str | None = None
    symbol: str | None = None
    id: int | None = None
    timestamp: datetime | None = None

    @model_validator(mode='before')
    @classmethod
    def map_ticker_to_symbol(cls, values):
        if isinstance(values, dict) and 'symbol' not in values and 'ticker' in values:
            values['symbol'] = values['ticker']
        return values
