from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai import Conversation
import logging
from typing import Dict, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class ElevenLabsService:
    def __init__(self):
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        if settings.elevenlabs_api_key:
            try:
                self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
                logger.info("ElevenLabs client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs client: {str(e)}")
                raise
        else:
            logger.warning("ElevenLabs API key not configured")
    
    async def create_conversation(self, agent_id: str, audio_interface) -> Conversation:
        if not self.client:
            raise ValueError("ElevenLabs client not initialized")
        
        try:
            conversation = Conversation(
                client=self.client,
                agent_id=agent_id,
                audio_interface=audio_interface
            )
            
            logger.info(f"Created conversation with agent {agent_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def end_conversation(self, conversation: Conversation):
        try:
            await conversation.end()
            logger.info("Conversation ended")
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")


elevenlabs_service = ElevenLabsService()