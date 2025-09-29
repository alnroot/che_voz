from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict
from pydantic import BaseModel

from domain.services import call_session_service
from services.agent_service import agent_service

router = APIRouter(tags=["Conversations"])


# Request/Response Models
class CallInitRequest(BaseModel):
    caller_phone: str
    caller_name: Optional[str] = None
    country_code: Optional[str] = "AR"
    language: Optional[str] = "es-AR"
    custom_context: Optional[Dict] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    agent_id: str
    agent_name: str
    websocket_url: str


class CallRequest(BaseModel):
    phone_number: str
    caller_info: Optional[Dict] = None


@router.post("/conversation/init", response_model=ConversationResponse)
async def initialize_conversation(request: CallInitRequest):
    """Initialize a conversation with an ElevenLabs agent"""
    try:
        session = await call_session_service.initialize_session(
            caller_phone=request.caller_phone,
            country_code=request.country_code,
            caller_name=request.caller_name,
            custom_context=request.custom_context
        )
        
        return ConversationResponse(
            conversation_id=session.conversation_id,
            agent_id=session.agent_id,
            agent_name=session.agent_name,
            websocket_url=f"/ws/conversation/{session.conversation_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing conversation: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/status")
async def get_conversation_status(conversation_id: str):
    """Get the status of a conversation"""
    session = call_session_service.get_session(conversation_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "conversation_id": conversation_id,
        "status": session.status,
        "agent_name": session.agent_name,
        "language": session.language
    }


@router.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """Manually end a conversation"""
    session = call_session_service.get_session(conversation_id)
    if session:
        await call_session_service.end_session(conversation_id)
        return {"message": "Conversation ended"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )


@router.post("/call/dial", response_model=ConversationResponse)
async def dial_number(request: CallRequest):
    """Dial a number and connect with the appropriate agent"""
    try:
        # Detect country from phone number
        phone_number = request.phone_number.replace(" ", "").replace("-", "")
        country_code = _detect_country_code(phone_number)
        
        # Create call initialization request
        call_init = CallInitRequest(
            caller_phone=request.phone_number,
            country_code=country_code,
            language=agent_service.get_agent_by_country(country_code).language
        )
        
        return await initialize_conversation(call_init)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error dialing number: {str(e)}"
        )


def _detect_country_code(phone_number: str) -> str:
    """Detect country code from phone number"""
    clean_number = phone_number.replace(" ", "").replace("-", "")
    
    # Special testing numbers
    if clean_number == "111":
        return "AR"  # Argentine agent
    elif clean_number == "444":
        return "AR_CBA"  # Cordoba agent
    elif clean_number == "222":
        return "MX"  # Mexican agent
    elif clean_number == "333":
        return "CO"  # Colombian agent
    elif clean_number == "555":
        return "MENDOCINO"  # Mendocino agent
    # Detect country by code
    elif clean_number.startswith("+54") or clean_number.startswith("54"):
        return "AR"  # Argentina
    elif clean_number.startswith("+52") or clean_number.startswith("52"):
        return "MX"  # Mexico
    elif clean_number.startswith("+57") or clean_number.startswith("57"):
        return "CO"  # Colombia
    else:
        return "AR"  # Default to Argentina