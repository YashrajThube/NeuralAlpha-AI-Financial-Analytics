import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.services.market_data_service import MarketDataService
from app.utils.helpers import success_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/tickers', response_model=ApiResponse)
async def list_tickers(db: AsyncSession = Depends(get_db)) -> ApiResponse:
    try:
        symbols = await MarketDataService.list_symbols(db)
        return success_response({'symbols': symbols, 'count': len(symbols)})
    except Exception:
        logger.exception('tickers_fallback')
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']
        return success_response(
            {'symbols': symbols, 'count': len(symbols)},
            message='Tickers served from fallback because market data storage is unavailable.',
        )
