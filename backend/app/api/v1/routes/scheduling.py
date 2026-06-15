from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.scheduling import ScheduleEventRequest
from app.services.public_user_service import PublicUserService
from app.services.scheduling_service import SchedulingService
from app.utils.helpers import success_response

router = APIRouter()


@router.post('/calendar/schedule', response_model=ApiResponse)
async def schedule_event(
    payload: ScheduleEventRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    current_user = await PublicUserService.get_or_create(db)
    result = await SchedulingService.create_event(payload, current_user, db)
    return success_response(result.model_dump())


@router.get('/calendar/events', response_model=ApiResponse)
async def list_events(
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    current_user = await PublicUserService.get_or_create(db)
    result = await SchedulingService.list_events(current_user, db)
    return success_response([item.model_dump() for item in result])
