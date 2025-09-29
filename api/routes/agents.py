from fastapi import APIRouter
from services.agent_service import agent_service

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("")
async def list_available_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "country_code": code,
                "agent_id": agent.agent_id,
                "name": agent.name,
                "language": agent.language
            }
            for code, agent in agent_service.get_all_agents().items()
        ]
    }