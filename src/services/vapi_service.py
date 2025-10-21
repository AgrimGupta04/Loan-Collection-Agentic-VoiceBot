import os
import requests

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")

def start_phone_call(customer_phone: str) -> dict:
    """
    Initiates a phone call to a customer using the Vapi API.

    Args:
        customer_phone (str): The phone number to call.

    Returns:
        dict: The JSON response from the Vapi API.
    
    Raises:
        ValueError: If Vapi configuration is missing.
        requests.exceptions.RequestException: If the API call fails.
    """
    if not all([VAPI_API_KEY, VAPI_ASSISTANT_ID]):
        raise ValueError("Vapi API Key or Assistant ID is not configured in environment variables.")

    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}
    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "customer": {"number": customer_phone}
    }

    print(f"VapiService: Initiating call to {customer_phone}...")
    response = requests.post("https://api.vapi.ai/call/phone", headers=headers, json=payload)
    
    # Raise an exception if the call fails (e.g., 400, 500 status codes)
    response.raise_for_status()
    
    print("VapiService: Call initiated successfully.")
    return response.json()