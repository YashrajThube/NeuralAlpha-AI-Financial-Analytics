from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class ModelType(str, Enum):
    ML = 'ml'
    DL = 'dl'
    ENSEMBLE = 'ensemble'


@dataclass
class Prediction:
    id: UUID | int
    user_id: UUID | int
    ticker: str
    model_type: ModelType | str
    predicted_value: float
    confidence_score: float
    features_used: dict | None = field(default_factory=dict)
    created_at: datetime | None = None
