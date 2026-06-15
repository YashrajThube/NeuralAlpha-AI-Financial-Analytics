from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1, max_length=4000)
    symbol: str = Field(default='AAPL', min_length=1, max_length=16, pattern='^[A-Za-z0-9._-]{1,16}$')

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

    @field_validator('message')
    @classmethod
    def normalize_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError('message cannot be blank')
        return cleaned


class ChatData(BaseModel):
    reply: str
    symbol: str
