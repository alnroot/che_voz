from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketState
import logging
import asyncio
import json
import base64

from domain.services import call_session_service, voice_call_service
from services.agent_service import agent_service
from api.routes.conversations import CallInitRequest, _detect_country_code

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def simple_websocket(websocket: WebSocket):
    """Simple WebSocket endpoint for minimalist dialer"""
    await websocket.accept()
    conversation = None
    conversation_id = None
    
    try:
        logger.info("New WebSocket connection established")
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "start_call":
                # Initialize conversation
                from_number = data.get("from_number")
                to_number = data.get("to_number")
                
                logger.info(f"Starting call from {from_number} to {to_number}")
                
                country_code = _detect_country_code(from_number.replace(" ", "").replace("-", ""))
                
                # Create call init request
                call_init = CallInitRequest(
                    caller_phone=from_number,
                    country_code=country_code,
                    language=agent_service.get_agent_by_country(country_code).language
                )
                
                # Initialize conversation
                session = await call_session_service.initialize_session(
                    caller_phone=call_init.caller_phone,
                    country_code=call_init.country_code,
                    caller_name=call_init.caller_name,
                    custom_context=call_init.custom_context
                )
                conversation_id = session.conversation_id
                
                # Create audio interface
                class SimpleAudioInterface:
                    def __init__(self, ws: WebSocket):
                        self.ws = ws
                        
                    async def send_audio(self, audio_data: bytes):
                        await self.ws.send_json({
                            "type": "audio",
                            "data": base64.b64encode(audio_data).decode('utf-8')
                        })
                
                # Create ElevenLabs conversation
                audio_interface = SimpleAudioInterface(websocket)
                conversation = await voice_call_service.create_conversation(session, audio_interface)
                
                # Start conversation task
                conversation_task = asyncio.create_task(conversation.start())
                await asyncio.sleep(0.5)
                
                await websocket.send_json({
                    "type": "call_started",
                    "conversation_id": conversation_id,
                    "agent_name": session.agent_name
                })
                
            elif message_type == "audio" and conversation:
                audio_data = base64.b64decode(data["data"])
                await conversation.send_audio(audio_data)
                
            elif message_type == "interrupt" and conversation:
                await conversation.interrupt()
                
            elif message_type == "end_call":
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Cleanup
        if conversation:
            await voice_call_service.end_conversation(conversation)
        if conversation_id:
            await call_session_service.end_session(conversation_id)
        await websocket.close()


@router.websocket("/ws/conversation/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    conversation = None
    
    try:
        # Get session
        session = call_session_service.get_session(conversation_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid conversation ID"
            })
            await websocket.close()
            return
        
        logger.info(f"Starting WebSocket for conversation {conversation_id}")
        
        # Update status
        call_session_service.update_session_status(conversation_id, "active")
        
        # Create audio interface for frontend
        class FrontendAudioInterface:
            def __init__(self, ws: WebSocket):
                self.ws = ws
                
            async def send_audio(self, audio_data: bytes):
                await self.ws.send_json({
                    "type": "audio",
                    "data": base64.b64encode(audio_data).decode('utf-8')
                })
                
            async def receive_audio(self):
                while True:
                    message = await self.ws.receive_json()
                    if message["type"] == "audio":
                        yield base64.b64decode(message["data"])
                    elif message["type"] == "end":
                        break
        
        # Create ElevenLabs conversation
        audio_interface = FrontendAudioInterface(websocket)
        conversation = await voice_call_service.create_conversation(session, audio_interface)
        
        # Start conversation in background
        try:
            conversation_task = asyncio.create_task(conversation.start())
            await asyncio.sleep(0.5)
            
            # Send ready signal
            await websocket.send_json({
                "type": "ready",
                "agent_name": session.agent_name,
                "language": session.language
            })
            logger.info(f"Sent ready signal for conversation {conversation_id}")
            
            # Wait for conversation to complete
            await conversation_task
            
        except Exception as e:
            logger.error(f"Error in conversation: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to connect to voice assistant"
            })
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        # Clean up
        if conversation:
            await voice_call_service.end_conversation(conversation)
        if conversation_id:
            await call_session_service.end_session(conversation_id)
        # Only close if still open
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()