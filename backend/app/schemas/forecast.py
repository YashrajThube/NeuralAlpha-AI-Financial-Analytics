from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ForecastRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symbol: str = Field(min_length=1, max_length=16, pattern='^[A-Za-z0-9._-]{1,16}$')
    horizon_days: int = Field(default=7, ge=1, le=30)

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


class ForecastData(BaseModel):
    symbol: str
    horizon_days: int
    forecast: list[float]
