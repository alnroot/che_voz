"""
Conversation service using Repository pattern for persistence
"""
import os
from typing import List, Optional, Dict
from datetime import datetime
import logging

from models.conversation import ConversationHistory, ConversationSummary
from infrastructure.conversation_repository import ConversationRepository, FileSystemConversationRepository
from infrastructure.base_patterns import SingletonMeta

logger = logging.getLogger(__name__)


class ConversationService(metaclass=SingletonMeta):
    """Singleton service for managing conversations using Repository pattern"""
    
    def __init__(self):
        # Initialize with filesystem repository by default
        storage_dir = "conversation_history"
        self._repository: ConversationRepository = FileSystemConversationRepository(storage_dir)
        logger.info(f"ConversationService initialized with FileSystemRepository at {storage_dir}")
        
        # Active conversations cache
        self._active_conversations: Dict[str, ConversationHistory] = {}
    
    async def start_conversation(self, conversation_data: dict) -> ConversationHistory:
        """Start tracking a new conversation"""
        conversation = ConversationHistory(
            conversation_id=conversation_data.get("conversation_id", conversation_data.get("id")),
            agent_id=conversation_data["agent_id"],
            agent_name=conversation_data.get("agent_name", "Unknown Agent"),
            caller_phone=conversation_data["caller_phone"],
            caller_name=conversation_data.get("caller_name"),
            language=conversation_data.get("language", "es-AR"),
            country_code=conversation_data.get("country_code", "AR"),
            metadata=conversation_data.get("custom_context"),
            status="active"
        )
        
        # Store in active cache
        self._active_conversations[conversation.conversation_id] = conversation
        
        # Persist
        await self._repository.save(conversation)
        
        logger.info(f"Started tracking conversation: {conversation.conversation_id}")
        return conversation
    
    async def add_message(self, conversation_id: str, speaker: str, text: str, 
                         audio_duration: Optional[float] = None):
        """Add a message to an active conversation"""
        # Check active cache first
        if conversation_id in self._active_conversations:
            conversation = self._active_conversations[conversation_id]
        else:
            # Load from repository
            conversation = await self._repository.find_by_id(conversation_id)
            if conversation:
                self._active_conversations[conversation_id] = conversation
            else:
                logger.error(f"Conversation not found: {conversation_id}")
                return
        
        # Add message
        conversation.add_message(speaker, text, audio_duration)
        
        # Save updated conversation
        await self._repository.save(conversation)
    
    async def end_conversation(self, conversation_id: str):
        """Mark a conversation as ended"""
        conversation = None
        
        # Check active cache
        if conversation_id in self._active_conversations:
            conversation = self._active_conversations[conversation_id]
        else:
            # Try to load from repository
            conversation = await self._repository.find_by_id(conversation_id)
        
        if not conversation:
            logger.warning(f"Trying to end unknown conversation: {conversation_id}")
            return
        
        # Update status and end time
        conversation.end_time = datetime.utcnow()
        conversation.status = "ended"
        
        # Save final state
        await self._repository.save(conversation)
        
        # Remove from active cache
        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]
        
        logger.info(f"Ended conversation: {conversation_id}")
    
    async def get_conversation_details(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get full details of a conversation"""
        # Check active cache first
        if conversation_id in self._active_conversations:
            return self._active_conversations[conversation_id]
        
        # Load from repository
        return await self._repository.find_by_id(conversation_id)
    
    async def get_recent_conversations(self, limit: int = 10) -> List[ConversationSummary]:
        """Get summaries of recent conversations"""
        return await self._repository.find_recent(limit)
    
    async def get_conversations_by_phone(self, phone_number: str) -> List[ConversationSummary]:
        """Get all conversations for a specific phone number"""
        return await self._repository.find_by_phone(phone_number)
    
    def set_repository(self, repository: ConversationRepository):
        """Set a different repository implementation (useful for testing)"""
        self._repository = repository
        logger.info(f"Repository changed to: {type(repository).__name__}")


# Singleton instance
conversation_service = ConversationService()