from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.services.genai_service import GenAIService


def get_genai_service():
    return GenAIService()


__all__ = ['get_db', 'get_current_user', 'require_role', 'get_genai_service']