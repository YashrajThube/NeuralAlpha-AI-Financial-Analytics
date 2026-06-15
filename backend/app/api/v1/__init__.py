from fastapi import APIRouter

from app.api.v1.routes import auth, chat, forecast, monitoring, portfolio, prediction, scheduling, sentiment, tickers

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_v1_router.include_router(prediction.router, tags=['prediction'])
api_v1_router.include_router(forecast.router, tags=['forecast'])
api_v1_router.include_router(sentiment.router, tags=['sentiment'])
api_v1_router.include_router(chat.router, tags=['chat'])
api_v1_router.include_router(monitoring.router, tags=['monitoring'])
api_v1_router.include_router(portfolio.router, tags=['portfolio'])
api_v1_router.include_router(scheduling.router, tags=['scheduling'])
api_v1_router.include_router(tickers.router, tags=['tickers'])
