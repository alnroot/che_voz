from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
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
import uuid

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


@app.get("/")
async def root():
    return {"message": "Welcome to LangGraph API Service with Twilio Integration"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "twilio_configured": bool(settings.twilio_account_sid)
    }


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


@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    try:
        return TTSResponse(
            audio_url=None,
            audio_base64=None,
            error="TTS functionality not implemented yet"
        )
    except Exception as e:
        logger.error(f"Error in TTS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in TTS: {str(e)}"
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