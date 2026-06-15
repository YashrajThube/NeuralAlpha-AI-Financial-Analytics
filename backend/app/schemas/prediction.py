from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PredictionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(min_length=1, max_length=16, pattern='^[A-Za-z0-9._-]{1,16}$')
    model_type: str = Field(default='ml', pattern='^(ml|dl|ensemble)$')

    @model_validator(mode='before')
    @classmethod
    def map_ticker_to_symbol(cls, values):
        if isinstance(values, dict) and 'symbol' not in values and 'ticker' in values:
            values['symbol'] = values['ticker']
        return values

    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class PredictionData(BaseModel):
    id: int
    symbol: str
    model_type: str
    predicted_value: float
    confidence_score: float
    timestamp: datetime
