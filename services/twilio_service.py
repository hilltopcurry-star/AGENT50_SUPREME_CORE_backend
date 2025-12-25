from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    def __init__(self):
        # Placeholders - Ali will update later
        self.account_sid = "AC_PLACEHOLDER" 
        self.auth_token = "AUTH_PLACEHOLDER"
        self.from_number = "+1234567890"
        
    def send_sms(self, to_number: str, message: str):
        try:
            # Client init only when keys are real
            if self.account_sid == "AC_PLACEHOLDER":
                logger.info(f"SIMULATION SMS to {to_number}: {message}")
                return True
                
            client = Client(self.account_sid, self.auth_token)
            client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return True
        except Exception as e:
            logger.error(f"Twilio Error: {e}")
            return False

twilio_service = TwilioService()