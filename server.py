import tempfile
import os
import requests
import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile, Request # Added Request for middleware
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import time # Added for middleware timing
import json # Added for pretty printing dicts

# Import custom modules
from src.database import Database
from src.services import vapi_service
from src.services import transcription_service
from src.dialogue_agent import Dialogue_agent
from src.action_agent import Action_agent
from src.sentiment_agent import Sentiment_agent
from src.services.mcp_service import lookup_number

from pydantic import BaseModel, Field
from datetime import date

class CustomerCreate(BaseModel):
    name: str
    phone: str
    due_date: date # Pydantic automatically validates YYYY-MM-DD
    loan_amount: float = Field(..., gt=0) # Ensure loan amount is positive

##  Initialization 
print("Initializing FastAPI App.")
app = FastAPI(title="Loan Collection AI Agent API")

print("Initializing Database...")
db = Database()
print("Initializing Dialogue Agent...")
dialogue_agent = Dialogue_agent()
print("Initializing Action Agent...")
action_agent = Action_agent()
print("Initializing Sentiment Agent...")
sentiment_agent = Sentiment_agent()

conversation_histories = defaultdict(list)
print("Initialization Complete.")

##  Middleware for Logging Requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"--> Incoming Request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"<-- Response Status: {response.status_code} for {request.url.path} (took {process_time:.4f}s)")
    except Exception as e:
        process_time = time.time() - start_time
        print(f"<-- EXCEPTION during request {request.url.path} (took {process_time:.4f}s): {e}")
        ## Re-raise the exception so FastAPI handles it
        raise e
    return response

##  CORS Middleware
print("Adding CORS Middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  ## For development. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##  Health Check Endpoint 
@app.get("/health")
def health():
    print("--- Health Check Endpoint Hit ---")
    return {"status": "ok"}

##  Frontend Endpoints

@app.get("/all-customers")
def get_all_customers():
    """Endpoint to retrieve all customers from the database."""
    print("GET /all-customers Endpoint Hit.")
    try:
        customers = db.fetch_all_customers()
        print(f"Retrieved {len(customers)} customers.")
        return {"customers": customers}
    except Exception as e:
        print(f"ERROR in /all-customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch all customers")

@app.get("/pending-customers")
def get_pending_customers():
    """Endpoint to retrieve pending customers from the database."""
    print("GET /pending-customers Endpoint Hit.")
    try:
        customers = db.fetch_due_customers()
        print(f"Retrieved {len(customers)} pending customers.")
        return {"customers": customers}
    except Exception as e:
        print(f"ERROR in /pending-customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending customers")


@app.post("/start-call/{customer_id}")
async def start_customer_call(customer_id: int):
    """Endpoint for Frontend to trigger a call to a specific customer."""
    print(f"POST /start-call/{customer_id} Endpoint Hit ")
    
    print(f"Fetching customer data for ID: {customer_id}")
    customer = db.fetch_customer_by_id(customer_id)  ## Corrected function name

    if not customer:
        print(f"ERROR: Customer not found for ID: {customer_id}")
        raise HTTPException(status_code = 404, detail = "Customer not found.")
    
    customer_phone = customer.get("phone")
    customer_name = customer.get("name")
    print(f"Customer found: {customer_name}, Phone: {customer_phone}")

    print(f"Validating phone number {customer_phone} using twilio lookup.")
    lookup_result = lookup_number(customer_phone)

    print(f"Twilio Lookup Result: {lookup_result}")

    if not lookup_result or not lookup_result.get("valid"):
        print(f"ERROR: Phone number {customer_name} is invalid or lookup failed.")
        raise HTTPException(status_code=400, detail=f"Phone number {customer_phone} is not valid.")
    
    number_type = lookup_result.get("type", "unknown")
    if number_type != 'mobile':
        # Log a warning instead of raising an error
        print(f"WARNING: Phone number {customer_phone} is not 'mobile' (Type: {number_type}). Proceeding anyway.")
    
    print(f"Phone number {customer_phone} validated successfully. (Type: {number_type})")
    
    try:

        print(f"Calling vapi_service.start_phone_call for {customer_name} at {customer_phone}")
        call_data = vapi_service.start_phone_call(customer_phone = customer_phone)
        print(f"Vapi call initiated successfully. Response: {call_data}")

        return {"status": "success", "message": f"Call initiated to {customer_name}", "call_data": call_data}
    except Exception as e:
        print(f"ERROR during Vapi call initiation for customer {customer_id}: {e}")
        raise HTTPException(status_code = 500, detail = str(e))
    

@app.post("/webhook/vapi")
async def handle_vapi_webhook(request_body: dict):
    """
    This is the main webhook that Vapi calls during the live conversation.
    """
    print("POST /webhook/vapi Endpoint Hit.")
    # print(f"Received Vapi Webhook Body:\n{json.dumps(request_body, indent=2)}") # Uncomment for very detailed logs

    message_type = request_body.get('message', {}).get('type')
    call_info = request_body.get('call', {})
    call_id = call_info.get('id', 'unknown_call')

    print(f"Webhook Call ID: {call_id}, Message Type: {message_type}")

    if message_type == 'transcript' and request_body['message']['role'] == 'user':
        transcript = request_body['message']['transcript']
        print(f"Call ID {call_id} - User Transcript: '{transcript}'")

        customer_phone = call_info.get('customer', {}).get('number')
        if not customer_phone:
            print(f"ERROR: No customer phone number in Vapi webhook for Call ID {call_id}")
            return {"reply": "Sorry, I couldn't identify your number."}

        print(f"Call ID {call_id} - Fetching customer data for phone: {customer_phone}")
        customer_data = db.get_customer_by_phone(customer_phone)

        if not customer_data:
            print(f"ERROR: Customer with phone {customer_phone} not found for Call ID {call_id}")
            return {"reply": "Sorry, I can't find your details in our system."}
        
        customer_id_internal = customer_data.get('id')
        print(f"Call ID {call_id} - Found Customer ID: {customer_id_internal}")

        ## Sentiment Feature 
        print(f"Call ID {call_id} - Analyzing sentiment for transcript")
        sentiment = sentiment_agent.analyze_sentiment(transcript)
        print(f"Call ID {call_id} - Sentiment Analysis Result: {sentiment}")

        ## Memory Feature
        conversation_histories[call_id].append(f"User: {transcript}")
        current_history = conversation_histories[call_id]
        print(f"Call ID {call_id} - Current History Length: {len(current_history)}")

        print(f"Call ID {call_id} - Calling dialogue_agent.get_next_action.(with sentiment analysis)")
        action_plan = dialogue_agent.get_next_action(transcript, customer_data, current_history, sentiment = sentiment)
        print(f"Call ID {call_id} - Received Action Plan:\n{json.dumps(action_plan, indent=2)}")

        response_to_vapi = {}
        intent = action_plan.get("intent", "UNCLEAR")

        if action_plan.get("action") == "SEQUENCE":
            print(f"Call ID {call_id} - Processing SEQUENCE action...")
            for i, action in enumerate(action_plan.get("payload", [])):
                action_type = action.get("type")
                print(f"Call ID {call_id} - Sequence Step {i+1}: Type={action_type}")

                if action_type == "REPLY":
                    reply_text = action.get("text")
                    response_to_vapi['reply'] = reply_text
                    conversation_histories[call_id].append(f"Agent: {reply_text}")
                    print(f"Call ID {call_id} - Added REPLY to Vapi response.")

                elif action_type == "SEND_SMS":
                    print(f"Call ID {call_id} - Calling action_agent to SEND_SMS...")
                    sms_success = action_agent.execute_action(action, customer_phone)
                    print(f"Call ID {call_id} - SMS Action Success: {sms_success}")
                    if sms_success:
                        print(f"Call ID {call_id} - Logging SMS_SENT to DB for customer {customer_id_internal}...")
                        db.log_call_outcome(customer_id_internal, "SMS_SENT", action.get("message"))

                elif action_type == "END_CALL":
                    end_text = action.get("text")
                    response_to_vapi = {"endCall": True, "endCallMessage": end_text}
                    conversation_histories[call_id].append(f"Agent: {end_text}")
                    print(f"Call ID {call_id} - Added END_CALL to Vapi response. Breaking sequence.")
                    break # Stop processing sequence after END_CALL

        elif action_plan.get("action") == "END_CALL":
            text = action_plan['payload']['text']
            response_to_vapi = {"endCall": True, "endCallMessage": text}
            conversation_histories[call_id].append(f"Agent: {text}")
            print(f"Call ID {call_id} - Added END_CALL (standalone) to Vapi response.")

        elif action_plan.get("action") == "REPLY":
            text = action_plan['payload']['text']
            response_to_vapi['reply'] = text
            conversation_histories[call_id].append(f"Agent: {text}")
            print(f"Call ID {call_id} - Added REPLY (standalone) to Vapi response.")

        print(f"Call ID {call_id} - Final response to Vapi:\n{json.dumps(response_to_vapi, indent=2)}")
        return response_to_vapi
    
    elif message_type == 'call-end':
        print(f"Call ID {call_id} - Received 'call-end' event.")
        if call_id in conversation_histories:
            del conversation_histories[call_id]
            print(f"Call ID {call_id} - Cleaned up conversation history.")
        return {}
    
    else:
        print(f"Call ID {call_id} - Received unhandled message type: {message_type}")
        return {}


@app.post("/upload-recording/{customer_id}")
async def upload_recording(customer_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload the recording... (rest of docstring)
    """
    print(f"POST /upload-recording/{customer_id} Endpoint Hit.")
    
    print(f"Fetching customer data for ID: {customer_id}")
    customer_data = db.fetch_customer_by_id(customer_id) ## Use correct function name

    if not customer_data:
        print(f"ERROR: Customer not found for ID: {customer_id}")
        raise HTTPException(status_code = 404, detail = "Customer not found.")
    
    print(f"Customer found: {customer_data.get('name')}")
    temp_path = None

    try:
        ## Create temp file path
        with tempfile.NamedTemporaryFile(delete = False, suffix = ".wav") as tmp_file:
            temp_path = tmp_file.name
        print(f"Created temporary file: {temp_path}")

        ## Asynchronously write uploaded file content to temp file
        print(f"Writing uploaded file '{file.filename}' to temporary file...")
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        print(f"Finished writing to temporary file.")

        ## Transcribing audio
        print(f"Calling transcription_service for file: {temp_path}")
        transcript = transcription_service.transcribe_audio_file(temp_path)
        print(f"Transcription result: '{transcript}'")
        if transcript.startswith("[") and transcript.endswith("]"):
            print(f"ERROR: Transcription failed for customer {customer_id}. Detail: {transcript}")
            raise HTTPException(status_code = 500, detail = transcript)
        
        ## Get action plan from agent 
        print(f"Calling dialogue_agent.get_next_action for customer {customer_id}...")
        action_plan = dialogue_agent.get_next_action(transcript, customer_data)
        print(f"Received Action Plan:\n{json.dumps(action_plan, indent=2)}")

        intent = action_plan.get("intent", "UNCLEAR")
        final_db_status = "UNCLEAR"
        
        if intent == "AGREES_TO_PAY":
            final_db_status = "SUCCESSFUL"
        elif intent == "REFUSES_TO_PAY":
            final_db_status = "NEEDS FOLLOW-UP"
        
        print(f"Determined Final DB Status: {final_db_status}")

        ## Log outcome to database
        print(f"Logging outcome to DB for customer {customer_id}...")
        db.log_call_outcome(customer_id, final_db_status, transcript)
        print(f"DB logging complete.")

        ## Execute actions if needed
        actions_executed = []
        if action_plan.get("action") == "SEQUENCE":
            print(f"Processing SEQUENCE action for customer {customer_id}...")
            for i, action in enumerate(action_plan.get("payload", [])):
                action_type = action.get("type")
                print(f"Upload Sequence Step {i+1}: Type={action_type}")
                if action_type == "SEND_SMS":
                    print(f"Calling action_agent to SEND_SMS for customer {customer_id}...")
                    sms_success = action_agent.execute_action(action, customer_data.get("phone"))
                    print(f"SMS Action Success: {sms_success}")
                    if sms_success:
                        actions_executed.append(action)
        
        print(f"Returning success response for customer {customer_id}.")
        return {
            "status": "success",
            "customerId": customer_id,
            "transcript": transcript,
            "determinedIntent": intent,
            "finalDbStatus": final_db_status,
            "actionPlan": action_plan,
            "actionsExecuted": actions_executed
        }
    
    except Exception as e:
        print(f"ERROR in /upload-recording for customer {customer_id}: {e}")
        ## Log the full traceback for detailed debugging if needed
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ## Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            print(f"Cleaning up temporary file: {temp_path}")
            try:
                os.remove(temp_path)
                print("Temporary file removed.")
            except Exception as remove_err:
                print(f"ERROR removing temporary file {temp_path}: {remove_err}")

@app.post("/add-customer")
async def add_new_customer(customer: CustomerCreate):
    """
    EndPoint to add new customer
    """
    print("--- POST /add-customer Endpoint Hit ---")
    print(f"Received new customer data: {customer}")

    due_date_str = customer.due_date.strftime('%Y-%m-%d')

    new_id = db.add_customer(
        name=customer.name,
        phone=customer.phone,
        due_date=due_date_str,
        loan_amount=customer.loan_amount
    )

    if new_id is not None:
        print(f"Successfully added customer with ID: {new_id}")
        ## Return the ID and a success message
        return {"status": "success", "message": f"Customer '{customer.name}' added successfully.", "customerId": new_id}
    else:
        print("ERROR: Failed to add customer to the database.")
        raise HTTPException(status_code=500, detail="Failed to add customer to the database.")

print("FastAPI App Defined")