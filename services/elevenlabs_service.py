import httpx
import websockets
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional
from config.settings import settings
from services.conversation_service import conversation_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ElevenLabsConversationHandler:
    """Maneja la conversación real con ElevenLabs WebSocket"""
    
    def __init__(self, agent_id: str, frontend_websocket, conversation_id: str = None, api_key: str = None):
        self.agent_id = agent_id
        self.frontend_ws = frontend_websocket
        self.elevenlabs_ws = None
        self.is_active = False
        self.conversation_id = conversation_id
        # Use provided API key if available, otherwise fall back to default
        self.api_key = api_key if api_key else settings.elevenlabs_api_key
        
    async def get_signed_url(self) -> Optional[str]:
        """Obtiene una URL firmada para conectarse al agente"""
        try:
            async with httpx.AsyncClient() as client:
                # Using GET method with query parameter as per ElevenLabs docs
                response = await client.get(
                    f"https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={self.agent_id}",
                    headers={
                        "xi-api-key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Got signed URL for agent {self.agent_id}")
                    return data.get("signed_url")
                else:
                    logger.error(f"Failed to get signed URL: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting signed URL: {str(e)}")
            return None
    
    async def start(self):
        """Inicia la conexión con ElevenLabs"""
        try:
            # Obtener URL firmada
            signed_url = await self.get_signed_url()
            if not signed_url:
                raise Exception("Could not get signed URL")
            
            # Conectar al WebSocket de ElevenLabs
            self.elevenlabs_ws = await websockets.connect(signed_url)
            self.is_active = True
            logger.info("Connected to ElevenLabs WebSocket")
            
            # Send initial silence to trigger agent response
            await asyncio.sleep(0.5)
            initial_silence = {
                "user_audio_chunk": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="  # WAV silence
            }
            await self.elevenlabs_ws.send(json.dumps(initial_silence))
            logger.info("Sent initial silence to trigger agent greeting")
            
            # Iniciar el bridge bidireccional
            logger.info("Starting bidirectional audio bridge")
            
            # Create tasks for both directions
            forward_task = asyncio.create_task(self.forward_to_elevenlabs())
            receive_task = asyncio.create_task(self.forward_from_elevenlabs())
            
            # Wait for either task to complete (or fail)
            done, pending = await asyncio.wait(
                [forward_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                
            # Check if any task failed
            for task in done:
                if task.exception():
                    logger.error(f"Task failed with exception: {task.exception()}")
                    raise task.exception()
            
        except Exception as e:
            logger.error(f"Error in ElevenLabs connection: {str(e)}")
            self.is_active = False
            raise
    
    async def forward_to_elevenlabs(self):
        """Reenvía audio del frontend a ElevenLabs"""
        try:
            chunks_sent = 0
            while self.is_active:
                # Recibir mensaje del frontend
                message = await self.frontend_ws.receive_json()
                logger.debug(f"Received message from frontend: {message.get('type')}")
                
                if message["type"] == "audio":
                    # Reenviar a ElevenLabs - el audio debe ser PCM 16000Hz
                    # Por ahora enviamos el audio tal cual viene del frontend
                    # TODO: Convertir a PCM 16000Hz si es necesario
                    audio_data = message["data"]
                    logger.debug(f"Received audio chunk from frontend, size: {len(audio_data) if audio_data else 0}")
                    
                    audio_message = {
                        "user_audio_chunk": audio_data  # base64 audio data
                    }
                    await self.elevenlabs_ws.send(json.dumps(audio_message))
                    chunks_sent += 1
                    logger.info(f"Sent audio chunk #{chunks_sent} to ElevenLabs")
                    
                elif message["type"] == "interrupt":
                    # Send interruption signal to ElevenLabs
                    interrupt_message = {
                        "type": "audio_input_override",
                        "audio_input_override_event": {
                            "interrupt_agent": True
                        }
                    }
                    await self.elevenlabs_ws.send(json.dumps(interrupt_message))
                    logger.info("Sent interrupt signal to ElevenLabs")
                    
                elif message["type"] == "end":
                    logger.info("Received end signal from frontend")
                    self.is_active = False
                    break
                    
        except Exception as e:
            logger.error(f"Error forwarding to ElevenLabs: {str(e)}")
            self.is_active = False
    
    async def forward_from_elevenlabs(self):
        """Reenvía respuestas de ElevenLabs al frontend"""
        try:
            messages_received = 0
            while self.is_active:
                # Recibir mensaje de ElevenLabs
                message = await self.elevenlabs_ws.recv()
                data = json.loads(message)
                messages_received += 1
                
                # Log the raw message for debugging
                logger.info(f"Message #{messages_received} from ElevenLabs, type: {data.get('type', 'unknown')}")
                logger.debug(f"Full message: {message[:200]}...")
                
                message_type = data.get("type", "")
                
                # Manejar diferentes tipos de mensajes según el formato real
                if message_type == "conversation_initiation_metadata":
                    metadata = data.get("conversation_initiation_metadata_event", {})
                    conversation_id = metadata.get("conversation_id")
                    logger.info(f"Conversation started: {conversation_id}")
                    # Notificar al frontend que la conversación está lista
                    await self.frontend_ws.send_json({
                        "type": "conversation_started",
                        "conversation_id": conversation_id
                    })
                    
                elif "audio_event" in data:
                    # Audio chunk del agente
                    audio_event = data["audio_event"]
                    audio_base64 = audio_event.get("audio_base_64")
                    if audio_base64:
                        logger.info(f"Received audio from ElevenLabs, size: {len(audio_base64)}")
                        await self.frontend_ws.send_json({
                            "type": "audio",
                            "data": audio_base64
                        })
                    else:
                        logger.warning("Received audio_event without audio_base_64")
                    
                elif message_type == "user_transcript":
                    # Transcripción del usuario
                    transcript_event = data.get("user_transcript_event", {})
                    transcript_text = transcript_event.get("user_transcript", "")
                    logger.info(f"User transcript: {transcript_text}")
                    
                    # Store in conversation history
                    if self.conversation_id and transcript_text:
                        await conversation_service.add_message(
                            self.conversation_id,
                            speaker="user",
                            text=transcript_text
                        )
                    
                    await self.frontend_ws.send_json({
                        "type": "user_transcript",
                        "text": transcript_text
                    })
                    
                elif message_type == "agent_response":
                    # Respuesta de texto del agente
                    response_event = data.get("agent_response_event", {})
                    agent_text = response_event.get("agent_response", "")
                    
                    # Store in conversation history
                    if self.conversation_id and agent_text:
                        await conversation_service.add_message(
                            self.conversation_id,
                            speaker="agent",
                            text=agent_text
                        )
                    
                    await self.frontend_ws.send_json({
                        "type": "agent_response",
                        "text": agent_text
                    })
                    
                elif message_type == "ping":
                    # Ignorar pings
                    logger.debug("Received ping from ElevenLabs")
                    
                elif "error" in data:
                    logger.error(f"ElevenLabs error: {data['error']}")
                    await self.frontend_ws.send_json({
                        "type": "error",
                        "message": data.get("error", "Unknown error")
                    })
                    
                else:
                    # Log unknown message types
                    logger.warning(f"Unknown message type from ElevenLabs: {message_type}")
                    logger.debug(f"Full unknown message: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("ElevenLabs WebSocket closed")
            self.is_active = False
        except Exception as e:
            logger.error(f"Error forwarding from ElevenLabs: {str(e)}")
            self.is_active = False
    
    async def send_audio(self, audio_data: bytes):
        """Método legacy - no usado con el nuevo approach"""
        pass
        
    async def receive_audio(self) -> AsyncGenerator[bytes, None]:
        """Método legacy - no usado con el nuevo approach"""
        yield b""
    
    async def end(self):
        """Termina la conversación"""
        self.is_active = False
        if self.elevenlabs_ws:
            await self.elevenlabs_ws.close()
        logger.info("ElevenLabs conversation ended")


class ElevenLabsService:
    def __init__(self):
        self._initialize_client()
        
    def _initialize_client(self):
        if settings.elevenlabs_api_key:
            logger.info("ElevenLabs API key configured")
        else:
            logger.warning("ElevenLabs API key not configured")
    
    async def create_conversation(self, agent_id: str, audio_interface, conversation_id: str = None, api_key: str = None):
        """Crea una conversación con el agente especificado"""
        try:
            # audio_interface aquí es el WebSocket del frontend
            conversation = ElevenLabsConversationHandler(agent_id, audio_interface.ws, conversation_id, api_key)
            # No iniciamos aquí, se inicia en el main
            logger.info(f"Created conversation handler for agent {agent_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def end_conversation(self, conversation):
        """Termina una conversación"""
        try:
            await conversation.end()
            logger.info("Conversation ended")
        except Exception as e:
            logger.error(f"Error ending conversation: {str(e)}")


elevenlabs_service = ElevenLabsService()