import os
import requests

# 1. LOAD NEW ENVIRONMENT VARIABLE
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID") # <-- ADD THIS LINE

def start_phone_call(customer_phone: str) -> dict:
    """
    Initiates a phone call to a customer using the Vapi API.
    ...
    """
    
    # 2. ADD DEBUG LOGS TO CHECK IF ENV VARS ARE LOADED
    # (We only print part of the key for security)
    print(f"VapiService: Using API Key (last 4 chars): ...{VAPI_API_KEY[-4:] if VAPI_API_KEY else 'NOT_SET'}")
    print(f"VapiService: Using Assistant ID: {VAPI_ASSISTANT_ID if VAPI_ASSISTANT_ID else 'NOT_SET'}")
    print(f"VapiService: Using Phone Number ID: {VAPI_PHONE_NUMBER_ID if VAPI_PHONE_NUMBER_ID else 'NOT_SET'}")

    # 3. UPDATE THE VALIDATION CHECK
    if not all([VAPI_API_KEY, VAPI_ASSISTANT_ID, VAPI_PHONE_NUMBER_ID]):
        raise ValueError("Vapi API Key, Assistant ID, or Phone Number ID is not configured in environment variables.")

    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}
    
    # 4. ADD THE MISSING 'phoneNumberId' TO THE PAYLOAD
    payload = {
        "assistantId": VAPI_ASSISTANT_ID,
        "phoneNumberId": VAPI_PHONE_NUMBER_ID, # <-- THIS IS THE FIX
        "customer": {"number": customer_phone}
    }

    print(f"VapiService: Initiating call to {customer_phone} with payload: {payload}")
    response = requests.post("https://api.vapi.ai/call/phone", headers=headers, json=payload)
    
    # Check for detailed error messages from Vapi
    if not response.ok:
        try:
            # Try to print the detailed error from Vapi's server
            error_detail = response.json()
            print(f"!!!!!!!!!!!!!! VAPI API ERROR !!!!!!!!!!!!!!")
            print(f"Vapi returned status {response.status_code} with detail: {error_detail}")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        except requests.exceptions.JSONDecodeError:
            # If Vapi sends a non-JSON error (like HTML)
            print(f"Vapi returned non-JSON error: {response.text}")
    
    # Raise an exception if the call fails (e.g., 400, 500 status codes)
    response.raise_for_status()
    
    print("VapiService: Call initiated successfully.")
    return response.json()