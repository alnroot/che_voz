from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "LangGraph API Service"
    debug: bool = False
    
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    numverify_api_key: Optional[str] = None
    
    redis_url: str = "redis://localhost:6379"
    
    websocket_url: str = "wss://localhost:8000/media-stream"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()