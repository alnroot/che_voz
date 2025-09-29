from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime


@dataclass
class CallSession:
    """Domain model for a voice call session"""
    conversation_id: str
    caller_phone: str
    agent_id: str
    agent_name: str
    country_code: str
    language: str
    status: str
    start_time: datetime
    caller_name: Optional[str] = None
    custom_context: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "conversation_id": self.conversation_id,
            "caller_phone": self.caller_phone,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "country_code": self.country_code,
            "language": self.language,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "caller_name": self.caller_name,
            "custom_context": self.custom_context
        }


@dataclass
class Agent:
    """Domain model for ElevenLabs agent configuration"""
    agent_id: str
    name: str
    language: str
    context: str
    country_code: str
    api_key: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "language": self.language,
            "context": self.context,
            "country_code": self.country_code,
            "api_key": self.api_key
        }