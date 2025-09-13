import requests
from fastapi import FastAPI, Form
from fastapi.responses import Response
from database import Database
from caller_agent import CallerAgent
from outcome_agent import Outcome_agent 

db = Database()
caller = CallerAgent(use_groq=True)
agent = Outcome_agent(use_groq=False)

app = FastAPI()

@app.get('/fetch_due_customers')
def fetch_pending_customers():
    """Fetch customers with pending call status."""
    customers = db.fetch_due_customers()
    return [
        {
            "id": c[0],
            "name": c[1],
            "phone": c[2],
            "due_date": c[3],
            "loan_amount": c[4],
            "call_status": c[5],
            "notes": c[6]
        }
        for c in customers
    ]

@app.post('/log_call_outcome')
def log_call_outcome_tool(customer_id, status, notes):
    """Log the outcome of a call for a specific customer."""
    db.log_call_outcome(customer_id, status, notes)
    return f"Logged outcome for customer ID {customer_id}: Status - {status}, Notes - {notes}"

@app.post('/twilio-voice')
def twilio_voice():
    """
        Twilio will call this when making a call.
        We tell Twilio to speak a message and record customer's response. 
    """

    twiml = """"
    <Response>
        <Say>Hello ! This is a call for loan payment reminder.Please pay as soon as possible.<Say>
        <Record maxLength = "15" action = "/twilio-recording" /> 
    </Response>
        """
    
    return Response(content=twiml, media_type="application/xml")    

@app.post('/twilio-recording')
def twilio_recording(recordingURL : str = Form(...), CallSid: str = Form(...), From: str = Form(...), To: str = Form(...), customer_id: int = Form(...)):
    """
    Twilio will call this afetr recording customer's response.
    """
    print(f"[Twilio] Recording available at: {recordingURL}")

    # 1. Download recording from Twilio
    audio_file = f"recording_{CallSid}.wav"
    recording_url_with_ext = recordingURL + ".wav"  # Twilio requires extension
    r = requests.get(recording_url_with_ext, auth=(caller.twilio_sid, caller.twilio_auth_token))
    with open(audio_file, "wb") as f:
        f.write(r.content)

    # 2. Transcribing with Google STT
    transcript = caller.transcribe_audio(audio_file)
    print(f"[Transcription] {transcript}")

    # 3. Classifing with Outcome_agent
    outcome = agent.process_customer(transcript, customer_id)
    print(f"[Outcome] {outcome}")

    # 4. Respond to Twilio (what the customer hears after speaking)
    twiml = f"""
    <Response>
        <Say>Thank you. We have noted your response as {outcome['status']}.</Say>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")
    