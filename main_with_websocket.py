from fastapi import FastAPI, HTTPException, status, WebSocket, Form, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
import json
from typing import Dict
from config.settings import settings
from models.schemas import (
    TextProcessRequest, 
    WorkflowResponse,
    TTSRequest, 
    TTSResponse,
    SMSRequest,
    SMSResponse,
    CallRequest,
    CallResponse,
    MessageStatusResponse,
    ProcessingStatus
)
from services.twilio_service import twilio_service
from services.geolocation_service import geolocation_service
from services.agent_mapping import agent_mapper
from services.redis_service import redis_service
from services.audio_bridge import TwilioAudioInterface, audio_bridge
from services.elevenlabs_service import elevenlabs_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await redis_service.get_client()
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    await redis_service.close()
    logger.info("Application shutdown")


@app.get("/")
async def root():
    return {"message": "Welcome to LangGraph API Service with Twilio-ElevenLabs Bridge"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "twilio_configured": bool(settings.twilio_account_sid),
        "elevenlabs_configured": bool(settings.elevenlabs_api_key),
        "redis_connected": bool(redis_service._client)
    }


@app.post("/twilio-webhook")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    try:
        logger.info(f"Incoming call from {From} to {To}, CallSid: {CallSid}")
        
        location_data = await geolocation_service.get_location(From)
        logger.info(f"Caller location: {location_data}")
        
        agent_config = agent_mapper.get_agent_by_country(location_data["country_code"])
        
        call_context = {
            "call_sid": CallSid,
            "caller": From,
            "called": To,
            "location": location_data,
            "agent_id": agent_config["agent_id"],
            "agent_config": agent_config,
            "status": CallStatus
        }
        
        await redis_service.set_call_context(CallSid, call_context)
        
        twiml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="{agent_config.get('language', 'en-US')}">
        Connecting you to our assistant. Please wait a moment.
    </Say>
    <Connect>
        <Stream url="{settings.websocket_url}">
            <Parameter name="callSid" value="{CallSid}"/>
        </Stream>
    </Connect>
</Response>'''
        
        return Response(content=twiml_response, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {str(e)}")
        error_twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>We're sorry, but we're experiencing technical difficulties. Please try again later.</Say>
    <Hangup/>
</Response>'''
        return Response(content=error_twiml, media_type="application/xml")


@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    websocket_id = str(uuid.uuid4())
    call_sid = None
    conversation = None
    
    try:
        twilio_interface = TwilioAudioInterface(websocket)
        
        async for message in websocket.iter_text():
            data = json.loads(message)
            
            if data["event"] == "start":
                call_sid = data["start"]["callSid"]
                await redis_service.set_websocket_mapping(websocket_id, call_sid)
                
                call_context = await redis_service.get_call_context(call_sid)
                if not call_context:
                    logger.error(f"No context found for call {call_sid}")
                    break
                
                agent_id = call_context["agent_id"]
                logger.info(f"Starting conversation with agent {agent_id} for call {call_sid}")
                
                conversation = await elevenlabs_service.create_conversation(
                    agent_id=agent_id,
                    audio_interface=twilio_interface
                )
                
                await audio_bridge.bridge_streams(twilio_interface, conversation)
                
            elif data["event"] == "stop":
                logger.info(f"Call ended for {call_sid}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        if conversation:
            await elevenlabs_service.end_conversation(conversation)
        if call_sid:
            await redis_service.delete_call_context(call_sid)
        await websocket.close()


@app.post("/process", response_model=WorkflowResponse)
async def process_text(request: TextProcessRequest):
    try:
        workflow_id = str(uuid.uuid4())
        
        return WorkflowResponse(
            id=workflow_id,
            status=ProcessingStatus.COMPLETED,
            result={"processed_text": request.text, "workflow": request.workflow_type}
        )
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}"
        )


@app.post("/twilio/sms", response_model=SMSResponse)
async def send_sms(request: SMSRequest):
    try:
        if not settings.twilio_account_sid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio service not configured"
            )
        
        result = twilio_service.send_sms(
            to_number=request.to_number,
            message=request.message
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send SMS")
            )
        
        return SMSResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending SMS: {str(e)}"
        )


@app.post("/twilio/call", response_model=CallResponse)
async def make_call(request: CallRequest):
    try:
        if not settings.twilio_account_sid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio service not configured"
            )
        
        result = twilio_service.make_call(
            to_number=request.to_number,
            twiml_url=request.twiml_url
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to make call")
            )
        
        return CallResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error making call: {str(e)}"
        )


@app.get("/twilio/message/{message_sid}", response_model=MessageStatusResponse)
async def get_message_status(message_sid: str):
    try:
        if not settings.twilio_account_sid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Twilio service not configured"
            )
        
        result = twilio_service.get_message_status(message_sid)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Message not found")
            )
        
        return MessageStatusResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting message status: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)