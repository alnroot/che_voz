from fastapi import FastAPI, HTTPException, status, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
import json
from typing import Dict, Optional
from config.settings import settings
from pydantic import BaseModel
from services.agent_mapping import agent_mapper
from services.elevenlabs_service import elevenlabs_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ElevenLabs Bridge API",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class CallInitRequest(BaseModel):
    caller_phone: str
    caller_name: Optional[str] = None
    country_code: Optional[str] = "US"
    language: Optional[str] = "en-US"
    custom_context: Optional[Dict] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    agent_id: str
    agent_name: str
    websocket_url: str


# Store active conversations
active_conversations = {}


@app.get("/")
async def root():
    return {"message": "ElevenLabs Bridge API"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "elevenlabs_configured": bool(settings.elevenlabs_api_key),
        "active_conversations": len(active_conversations)
    }


@app.post("/conversation/init", response_model=ConversationResponse)
async def initialize_conversation(request: CallInitRequest):
    """
    Initialize a conversation with ElevenLabs agent based on caller info
    Frontend calls this first to get the conversation details
    """
    try:
        # Get appropriate agent based on country
        agent_config = agent_mapper.get_agent_by_country(request.country_code)
        
        # Generate conversation ID
        conversation_id = str(uuid.uuid4())
        
        # Store conversation context
        active_conversations[conversation_id] = {
            "id": conversation_id,
            "caller_phone": request.caller_phone,
            "caller_name": request.caller_name,
            "country_code": request.country_code,
            "language": request.language,
            "agent_id": agent_config["agent_id"],
            "agent_config": agent_config,
            "custom_context": request.custom_context,
            "status": "initialized"
        }
        
        logger.info(f"Initialized conversation {conversation_id} with agent {agent_config['name']}")
        
        return ConversationResponse(
            conversation_id=conversation_id,
            agent_id=agent_config["agent_id"],
            agent_name=agent_config["name"],
            websocket_url=f"/ws/conversation/{conversation_id}"
        )
        
    except Exception as e:
        logger.error(f"Error initializing conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing conversation: {str(e)}"
        )


@app.websocket("/ws/conversation/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for audio streaming between frontend and ElevenLabs
    """
    await websocket.accept()
    conversation = None
    
    try:
        # Get conversation context
        context = active_conversations.get(conversation_id)
        if not context:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid conversation ID"
            })
            await websocket.close()
            return
        
        agent_id = context["agent_id"]
        logger.info(f"Starting WebSocket for conversation {conversation_id}")
        
        # Update status
        active_conversations[conversation_id]["status"] = "active"
        
        # Create audio interface for frontend
        class FrontendAudioInterface:
            def __init__(self, ws: WebSocket):
                self.ws = ws
                
            async def send_audio(self, audio_data: bytes):
                # Send audio to frontend
                await self.ws.send_json({
                    "type": "audio",
                    "data": audio_data.hex()  # Convert bytes to hex string
                })
                
            async def receive_audio(self):
                # Receive audio from frontend
                while True:
                    message = await self.ws.receive_json()
                    if message["type"] == "audio":
                        # Convert hex string back to bytes
                        yield bytes.fromhex(message["data"])
                    elif message["type"] == "end":
                        break
        
        # Create ElevenLabs conversation
        audio_interface = FrontendAudioInterface(websocket)
        conversation = await elevenlabs_service.create_conversation(
            agent_id=agent_id,
            audio_interface=audio_interface
        )
        
        # Send ready signal
        await websocket.send_json({
            "type": "ready",
            "agent_name": context["agent_config"]["name"],
            "language": context["language"]
        })
        
        # Handle bidirectional audio streaming
        async for message in websocket.iter_json():
            if message["type"] == "audio":
                # Forward audio to ElevenLabs
                audio_data = bytes.fromhex(message["data"])
                await conversation.send_audio(audio_data)
                
            elif message["type"] == "end":
                logger.info(f"Ending conversation {conversation_id}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up
        if conversation:
            await elevenlabs_service.end_conversation(conversation)
        if conversation_id in active_conversations:
            active_conversations[conversation_id]["status"] = "ended"
            del active_conversations[conversation_id]
        await websocket.close()


@app.get("/conversation/{conversation_id}/status")
async def get_conversation_status(conversation_id: str):
    """Get the status of a conversation"""
    context = active_conversations.get(conversation_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "conversation_id": conversation_id,
        "status": context["status"],
        "agent_name": context["agent_config"]["name"],
        "language": context["language"]
    }


@app.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """Manually end a conversation"""
    if conversation_id in active_conversations:
        active_conversations[conversation_id]["status"] = "ended"
        del active_conversations[conversation_id]
        return {"message": "Conversation ended"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )


@app.get("/agents")
async def list_available_agents():
    """List all available agents"""
    return {
        "agents": [
            {
                "country_code": code,
                "agent_id": config["agent_id"],
                "name": config["name"],
                "language": config["language"]
            }
            for code, config in agent_mapper.agent_map.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)