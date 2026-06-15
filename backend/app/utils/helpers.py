from app.schemas.common import ApiResponse


def success_response(data=None, message: str | None = None) -> ApiResponse:
    return ApiResponse(success=True, data=data, error=None, message=message)


def error_response(error: str, message: str | None = None) -> ApiResponse:
    return ApiResponse(success=False, data=None, error=error, message=message)
