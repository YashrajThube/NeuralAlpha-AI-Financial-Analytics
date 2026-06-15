from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService
from app.utils.helpers import success_response

router = APIRouter()


@router.post('/register', response_model=ApiResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    user = await AuthService.register(payload, db)
    return success_response({'id': user.id, 'email': user.email, 'role': user.role}, message='User created')


@router.post('/login', response_model=ApiResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> ApiResponse:
    token = await AuthService.login(payload, db)
    return success_response(token.model_dump(), message='Authentication successful')
