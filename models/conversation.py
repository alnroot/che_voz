from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ConversationMessage(BaseModel):
    """Represents a single message in a conversation"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker: str  # 'user' or 'agent'
    text: str
    audio_duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationSummary(BaseModel):
    """Summary of a conversation for dashboard display"""
    conversation_id: str
    agent_id: str
    agent_name: str
    caller_phone: str
    caller_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    message_count: int = 0
    language: str
    country_code: str
    status: str  # 'active', 'completed', 'error'
    

class ConversationHistory(BaseModel):
    """Complete conversation history with all messages"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_name: str
    caller_phone: str
    caller_name: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    language: str
    country_code: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    def add_message(self, speaker: str, text: str, audio_duration: Optional[float] = None):
        """Add a message to the conversation"""
        self.messages.append(ConversationMessage(
            speaker=speaker,
            text=text,
            audio_duration=audio_duration
        ))
        
    def get_summary(self) -> ConversationSummary:
        """Get a summary of this conversation"""
        duration = None
        if self.end_time and self.start_time:
            duration = int((self.end_time - self.start_time).total_seconds())
            
        status = "completed" if self.end_time else "active"
        
        return ConversationSummary(
            conversation_id=self.conversation_id,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            caller_phone=self.caller_phone,
            caller_name=self.caller_name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=duration,
            message_count=len(self.messages),
            language=self.language,
            country_code=self.country_code,
            status=status
        )