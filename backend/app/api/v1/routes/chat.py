from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import ChatRequest
from app.schemas.common import ApiResponse
from app.services.chat_service import ChatService
from app.utils.helpers import success_response

router = APIRouter()


@router.post('/chat', response_model=ApiResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    result = await ChatService.chat(payload, db)
    return success_response(result.model_dump())
