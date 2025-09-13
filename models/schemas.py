from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TextProcessRequest(BaseModel):
    text: str = Field(..., description="Text to process")
    workflow_type: str = Field(default="default", description="Type of workflow to execute")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Additional parameters")


class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice_id: Optional[str] = Field(None, description="ElevenLabs voice ID")
    model_id: Optional[str] = Field(default="eleven_monolingual_v1", description="ElevenLabs model")


class WorkflowResponse(BaseModel):
    id: str
    status: ProcessingStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    
class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    error: Optional[str] = None


class SMSRequest(BaseModel):
    to_number: str = Field(..., description="Recipient phone number in E.164 format (e.g., +1234567890)")
    message: str = Field(..., description="SMS message content", max_length=1600)


class SMSResponse(BaseModel):
    success: bool
    message_sid: Optional[str] = None
    status: Optional[str] = None
    to: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")
    body: Optional[str] = None
    date_created: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[int] = None


class CallRequest(BaseModel):
    to_number: str = Field(..., description="Recipient phone number in E.164 format")
    twiml_url: str = Field(..., description="URL returning TwiML instructions for the call")


class CallResponse(BaseModel):
    success: bool
    call_sid: Optional[str] = None
    status: Optional[str] = None
    to: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")
    date_created: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[int] = None


class MessageStatusResponse(BaseModel):
    success: bool
    sid: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    date_sent: Optional[str] = None
    date_updated: Optional[str] = None
    error: Optional[str] = None