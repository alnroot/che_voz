import base64
import asyncio
import logging
from typing import Optional, AsyncGenerator
from fastapi import WebSocket
import json

logger = logging.getLogger(__name__)


class TwilioAudioInterface:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.stream_sid = None
        self.call_sid = None
        
    async def send_audio_to_twilio(self, audio_data: bytes):
        try:
            payload = base64.b64encode(audio_data).decode('utf-8')
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {
                    "payload": payload
                }
            }
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending audio to Twilio: {str(e)}")
    
    async def receive_audio_from_twilio(self) -> AsyncGenerator[bytes, None]:
        try:
            while True:
                data = await self.websocket.receive_text()
                message = json.loads(data)
                
                if message["event"] == "connected":
                    logger.info("Twilio stream connected")
                    self.stream_sid = message.get("streamSid")
                    continue
                    
                elif message["event"] == "start":
                    logger.info("Twilio stream started")
                    self.call_sid = message["start"].get("callSid")
                    continue
                    
                elif message["event"] == "media":
                    audio_payload = message["media"]["payload"]
                    audio_data = base64.b64decode(audio_payload)
                    yield audio_data
                    
                elif message["event"] == "stop":
                    logger.info("Twilio stream stopped")
                    break
                    
        except Exception as e:
            logger.error(f"Error receiving audio from Twilio: {str(e)}")


class AudioBridge:
    def __init__(self):
        self.active_bridges = {}
        
    async def bridge_streams(self, twilio_interface: TwilioAudioInterface, elevenlabs_conversation):
        bridge_id = id(twilio_interface)
        self.active_bridges[bridge_id] = True
        
        try:
            async def twilio_to_elevenlabs():
                async for audio_chunk in twilio_interface.receive_audio_from_twilio():
                    if not self.active_bridges.get(bridge_id):
                        break
                    await elevenlabs_conversation.send_audio(audio_chunk)
            
            async def elevenlabs_to_twilio():
                async for audio_chunk in elevenlabs_conversation.receive_audio():
                    if not self.active_bridges.get(bridge_id):
                        break
                    await twilio_interface.send_audio_to_twilio(audio_chunk)
            
            await asyncio.gather(
                twilio_to_elevenlabs(),
                elevenlabs_to_twilio()
            )
            
        except Exception as e:
            logger.error(f"Error in audio bridge: {str(e)}")
        finally:
            del self.active_bridges[bridge_id]


audio_bridge = AudioBridge()