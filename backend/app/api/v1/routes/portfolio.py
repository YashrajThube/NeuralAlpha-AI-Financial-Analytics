from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.portfolio_service import PortfolioService
from app.services.public_user_service import PublicUserService
from app.utils.helpers import success_response

router = APIRouter()


class PortfolioUpsertRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    quantity: float = Field(gt=0)
    avg_price: float = Field(gt=0)
    current_price: float = Field(gt=0)


@router.get('/portfolio', response_model=ApiResponse)
async def portfolio_summary(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    current_user = await PublicUserService.get_or_create(db)
    result = await PortfolioService.summary(current_user, db)
    return success_response(result)


@router.post('/portfolio', response_model=ApiResponse)
async def portfolio_upsert(
    payload: PortfolioUpsertRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    current_user = await PublicUserService.get_or_create(db)
    result = await PortfolioService.upsert_position(
        current_user,
        payload.symbol,
        payload.quantity,
        payload.avg_price,
        payload.current_price,
        db,
    )
    return success_response(result, message='Portfolio updated')
