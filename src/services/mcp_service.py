import os 
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

try:
    if not all([TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        raise ValueError("Twilio credentials (SID, AUTH_TOKEN, PHONE_NUMBER) are not fully set.")
    
    twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    print("Twilio client initialized successfully.")

except ValueError as e:
    print(f"ERROR: {e}")
    twilio_client = None
except Exception as e:
    print(f"Twilio initialization error: {e}")
    twilio_client = None

def send_sms(to_number: str, message: str) -> bool:
    """
    Sends SMS using Twilio.

    This is the primary function needed by the ActionAgent to send payment links.

    Args:
        to_number (str): The recipient's phone number in E.164 format (e.g., "+14155552671").
        message (str): The content of the text message.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    if not twilio_client:
        print(" Cannot send SMS: Twilio client is not initialized.")
        return False
    
    try:
        twilio_client.messages.create(
            to = to_number,
            from_ = TWILIO_PHONE_NUMBER,
            body = message
        )

        print(f"SMS sent successfully to {to_number}")
        return True
    
    except TwilioRestException as e:
        print(f"Failed to send SMS to {to_number}. Twilio Error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while sending SMS to {to_number}: {e}")
        return False
    
def lookup_number(phone_number: str) -> dict | None:
    """
    Looks up information about a phone number using Twilio's Lookup API.

    This function can be used by a future "PreflightAgent" to validate a number
    before attempting to call or text it.

    Args:
        phone_number (str): The phone number to look up in E.164 format.

    Returns:
        dict | None: A dictionary with number details (e.g., {'valid': True, 'type': 'mobile'})
                      or None if the lookup fails.
    """

    if not twilio_client:
        print("Cannot lookup number since twilio client is not initialized.")
        return None
    
    try:
        lookup_data = twilio_client.lookups.v2.phone_numbers(phone_number).fetch()

        result = {
            "valid": lookup_data.valid,
            "phone_number": lookup_data.phone_number,
            "country_code": lookup_data.country_code,
            "type": lookup_data.line_type_intelligence.get('type') if lookup_data.line_type_intelligence else 'unknown'
        }

        print(f"Phone number lookup successful: {result}")
        return result
    
    except TwilioRestException as e:
        if e.status == 404:
            print(f"Phone number {phone_number} is not valid.")
        else:
            print(f"Phone Number lookup failed. Twilio Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during phone number lookup: {e}")
        return None