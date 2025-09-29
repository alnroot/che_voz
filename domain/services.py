import uuid
import logging
from datetime import datetime
from typing import Dict, Optional

from domain.models import CallSession, Agent
from services.agent_service import agent_service
from services.elevenlabs_service import elevenlabs_service
from services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


class CallSessionService:
    """Service for managing call sessions"""
    
    def __init__(self):
        self._active_sessions: Dict[str, CallSession] = {}
    
    async def initialize_session(self, caller_phone: str, country_code: str = "AR", 
                               caller_name: Optional[str] = None, 
                               custom_context: Optional[Dict] = None) -> CallSession:
        """Initialize a new call session"""
        try:
            agent = agent_service.get_agent_by_country(country_code)
            conversation_id = str(uuid.uuid4())
            
            session = CallSession(
                conversation_id=conversation_id,
                caller_phone=caller_phone,
                agent_id=agent.agent_id,
                agent_name=agent.name,
                country_code=country_code,
                language=agent.language,
                status="initialized",
                start_time=datetime.utcnow(),
                caller_name=caller_name,
                custom_context=custom_context
            )
            
            self._active_sessions[conversation_id] = session
            
            # Start tracking conversation history
            await conversation_service.start_conversation(session.to_dict())
            
            logger.info(f"Initialized session {conversation_id} with agent {agent.name}")
            return session
            
        except Exception as e:
            logger.error(f"Error initializing session: {str(e)}")
            raise
    
    def get_session(self, conversation_id: str) -> Optional[CallSession]:
        """Get an active session by ID"""
        return self._active_sessions.get(conversation_id)
    
    def update_session_status(self, conversation_id: str, status: str):
        """Update session status"""
        if conversation_id in self._active_sessions:
            self._active_sessions[conversation_id].status = status
    
    async def end_session(self, conversation_id: str):
        """End a call session"""
        if conversation_id in self._active_sessions:
            self._active_sessions[conversation_id].status = "ended"
            await conversation_service.end_conversation(conversation_id)
            del self._active_sessions[conversation_id]
            logger.info(f"Ended session {conversation_id}")
    
    def get_active_sessions(self) -> Dict[str, CallSession]:
        """Get all active sessions"""
        return {k: v for k, v in self._active_sessions.items() if v.status == "active"}


class VoiceCallService:
    """Service for handling voice call operations"""
    
    async def create_conversation(self, session: CallSession, audio_interface):
        """Create ElevenLabs conversation for a session"""
        try:
            agent = agent_service.get_agent_by_country(session.country_code)
            api_key = agent.api_key
            
            conversation = await elevenlabs_service.create_conversation(
                agent_id=session.agent_id,
                audio_interface=audio_interface,
                conversation_id=session.conversation_id,
                api_key=api_key
            )
            
            logger.info(f"Created ElevenLabs conversation for session {session.conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def end_conversation(self, conversation):
        """End ElevenLabs conversation"""
        try:
            await elevenlabs_service.end_conversation(conversation)
            logger.info("ElevenLabs conversation ended")
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")


# Service instances
call_session_service = CallSessionService()
voice_call_service = VoiceCallService()