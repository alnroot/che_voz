from fastapi import APIRouter
from domain.services import call_session_service
from config.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    active_sessions = call_session_service.get_active_sessions()
    return {
        "status": "healthy",
        "elevenlabs_configured": bool(settings.elevenlabs_api_key),
        "active_conversations": len(active_sessions)
    }