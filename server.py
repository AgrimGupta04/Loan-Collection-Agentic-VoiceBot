import tempfile
import os
import requests
import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict


from src.database import Database
from src.services import vapi_service
from src.services import transcription_service
from src.dialogue_agent import Dialogue_agent
from src.action_agent import Action_agent


app = FastAPI()
db = Database()
dialogue_agent = Dialogue_agent()
action_agent = Action_agent()

conversation_histories = defaultdict(list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/all-customers")
def get_all_customers():
    """Endpoint to retrieve all customers from the database."""

    customers = db.fetch_all_customers()
    return {"customers": customers}

@app.get("/pending-customers")
def get_pending_customers():
    """Endpoint to retrieve pending customers from the database."""

    customers = db.fetch_due_customers()
    return {"customers": customers}

@app.post("/start-call/{customer_id}")
async def start_customer_call(customer_id: int):
    """Endpoint for Frontend to trigger a call to a specific customer."""

    customer = db.fetch_customer_by_id(customer_id)
    if not customer:
        print("Customer not found in the Database.")
        raise HTTPException(status_code = 404, detail = "Customer not found.")
    
    try:
        customer_phone = customer.get("phone")
        customer_name = customer.get("name")

        call_data = vapi_service.start_phone_call(customer_phone = customer_phone)

        return {"status": "success", "message": f"Call initiated to {customer_name}", "call_data": call_data}
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
    

@app.post("/webhook/vapi")
async def handle_vapi_webhook(request_body: dict):
    """
    This is the main webhook that Vapi calls during the live conversation.
    """

    message_type = request_body.get('message', {}).get('type')

    if message_type == 'transcript' and request_body['message']['role'] == 'user':
        call_id = request_body['call']['id']
        transcript = request_body['message']['transcript']

        customer_phone = request_body['call']['customer']['number']
        customer_data = db.get_customer_by_phone(customer_phone)

        if not customer_data:
            print(f"Customer with phone {customer_phone} not found.")
            return {"reply": "Sorry, I can't find your details in our system."}

        conversation_histories[call_id].append(f"User: {transcript}")
        current_history = conversation_histories[call_id]

        action_plan = dialogue_agent.get_next_action(transcript, customer_data, current_history)
        response_to_vapi = {}

        intent = action_plan.get("intent", "UNCLEAR")

        if action_plan.get("action") == "SEQUENCE":
            for action in action_plan.get("payload", []):
                action_type = action.get("type")

                if action_type == "REPLY":
                    response_to_vapi['reply'] = action.get("text")
                    conversation_histories[call_id].append(f"Agent: {action.get('text')}")

                elif action_type == "SEND_SMS":
                    action_agent.execute_action(action, customer_phone)
                    db.log_call_outcome(customer_data['id'], "SMS_SENT", action.get("message"))

                elif action_type == "END_CALL":
                    response_to_vapi = {"endCall": True, "endCallMessage": action.get("text")}
                    conversation_histories[call_id].append(f"Agent: {action.get('text')}")
                    break

        elif action_plan.get("action") == "END_CALL":
            text = action_plan['payload']['text']
            response_to_vapi = {"endCall": True, "endCallMessage": text}
            conversation_histories[call_id].append(f"Agent: {text}")

        elif action_plan.get("action") == "REPLY":
            text = action_plan['payload']['text']
            response_to_vapi['reply'] = text
            conversation_histories[call_id].append(f"Agent: {text}")

        return response_to_vapi
    
    elif message_type == 'call-end':
        call_id = request_body['call']['id']
        if call_id in conversation_histories:
            del conversation_histories[call_id]
            print(f"Cleaned up conversation history for call {call_id}")
        return {}
    
    return {}


@app.post("/upload-recording/{customer_id}") 
async def upload_recording(customer_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload the recording of the call recieved from
    the frontend in the form of .wav and process the customer based on it and update the database.
    Not using conversation history of any kind.
    """
    
    customer_data = db.fetch_customer_by_id(customer_id)

    if not customer_data:
        raise HTTPException(status_code = 404, detail = "Customer not found.")
    
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete = False, suffix = ".wav") as tmp_file:
            temp_path = tmp_file.name
        
        async with aiofiles.open(temp_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        transcript = transcription_service.transcribe_audio_file(temp_path)
        if "[Transcription failed]" in transcript or "[Google API error]" in transcript:
            raise HTTPException(status_code = 500, detail = transcript)
        
        action_plan = dialogue_agent.get_next_action(transcript, customer_data)
        intent = action_plan.get("intent", "UNCLEAR")
        final_db_status = "UNCLEAR"
        
        if intent == "AGREES_TO_PAY":
            final_db_status = "SUCCESSFUL"
        elif intent == "REFUSES_TO_PAY":
            final_db_status = "NEEDS FOLLOW-UP"
        
        db.log_call_outcome(customer_id, final_db_status, transcript)

        actions_executed = []
        if action_plan.get("action") == "SEQUENCE":
            for action in action_plan.get("payload", []):
                if action.get("type") == "SEND_SMS":
                    action_agent.execute_action(action, customer_data.get("phone"))
                    actions_executed.append(action)
        
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ## IMPORTANT: Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
