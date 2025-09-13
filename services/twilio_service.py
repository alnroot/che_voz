from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Optional, Dict, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class TwilioService:
    def __init__(self):
        self.client = None
        self.from_number = settings.twilio_phone_number
        self._initialize_client()
    
    def _initialize_client(self):
        if settings.twilio_account_sid and settings.twilio_auth_token:
            try:
                self.client = Client(
                    settings.twilio_account_sid,
                    settings.twilio_auth_token
                )
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
                raise
        else:
            logger.warning("Twilio credentials not configured")
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("Twilio client not initialized. Check your credentials.")
        
        if not self.from_number:
            raise ValueError("Twilio phone number not configured")
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "date_created": message.date_created.isoformat() if message.date_created else None
            }
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": e.code
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def make_call(self, to_number: str, twiml_url: str) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("Twilio client not initialized. Check your credentials.")
        
        if not self.from_number:
            raise ValueError("Twilio phone number not configured")
        
        try:
            call = self.client.calls.create(
                url=twiml_url,
                to=to_number,
                from_=self.from_number
            )
            
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status,
                "to": call.to,
                "from": call.from_,
                "date_created": call.date_created.isoformat() if call.date_created else None
            }
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": e.code
            }
        except Exception as e:
            logger.error(f"Unexpected error making call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("Twilio client not initialized. Check your credentials.")
        
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                "success": True,
                "sid": message.sid,
                "status": message.status,
                "error_code": message.error_code,
                "error_message": message.error_message,
                "date_sent": message.date_sent.isoformat() if message.date_sent else None,
                "date_updated": message.date_updated.isoformat() if message.date_updated else None
            }
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": e.code
            }
        except Exception as e:
            logger.error(f"Unexpected error getting message status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


twilio_service = TwilioService()