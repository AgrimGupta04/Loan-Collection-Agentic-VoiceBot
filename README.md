# Loan Collection Agentic VoiceBot

An AI powered **VoiceBot** for automating loan repayment reminders.  
The system integrates **Groq (TTS + LLM)**, **Google STT**, **Twilio** (for phone calls), and **FastAPI** (for backend API).  
Built for hackathons to demonstrate an **agentic AI voice assistant** for loan collection workflows.

---

## Features
- **Database (SQLite)** with customer info (name, phone, due date, loan amount, status).
- **Automatic call reminders** using **Twilio**.
- **Speech-to-Text (STT)** transcription of customer responses.
- **LLM classification** of customer intent (Successful, Needs Follow up, Failed).
- **Text-to-Speech (TTS)** responses generated via **Groq TTS**.
- **FastAPI backend** for Twilio webhooks + customer management.
- **Streamlit frontend (optional)** for hackathon demo dashboards.

---

## Project Structure
```
.
├── app.py                # Main entrypoint (run pipeline, Twilio, or FastAPI)
├── database.py           # SQLite database setup + seeding
├── caller_agent.py       # Handles Twilio + Groq TTS + STT
├── outcome_agent.py      # Classifies customer responses
├── mcp_integration.py    # FastAPI backend (Twilio + DB APIs)
├── requirements.txt      # Dependencies
├── main.py               # For local Testing
├── .env                  # Secrets (Twilio, Groq, Ngrok)
└── README.md             # Project documentation
```

---

## Setup Instructions

### 1️. Clone Repo & Create Environment
```bash
git clone https://github.com/AgrimGupta04/Loan-Collection-Agentic-VoiceBot.git
cd Loan-Collection-Agentic-VoiceBot
python -m venv voice-bot-env
voice-bot-env\Scripts\activate   # (Windows)
# OR
source voice-bot-env/bin/activate # (Mac/Linux)
```

### 2️. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️. Configure Environment Variables
Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_verified_number
NGROK_AUTH_TOKEN=your_ngrok_token
```

**Important:**  
- Twilio phone number must be purchased/verified on your Twilio account.  
- Ngrok auth token from [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).  

---

## Running the Project

### Option 1: Local Test (Fake Pipeline)
Simulates a call with a local audio file (`user_says_he_will_pay.wav`).

```bash
python app.py --mode pipeline
```

---

### Option 2: Make a Real Twilio Call
Fetches first customer from DB and places a call.

```bash
python app.py --mode call
```

---

### Option 3: Run Backend (FastAPI)
Runs FastAPI backend for Twilio callbacks + frontend.

```bash
uvicorn app:app --reload --port 8000
```

Expose API to Twilio with ngrok:
```bash
ngrok http 8000
```

Copy the **public URL** and update it in your Twilio **Webhook settings**.

---

## Twilio Integration
- **/twilio-voice** → Twilio speaks reminder + records response.  
- **/twilio-recording** → Fetches recording → Transcribes → Classifies → Logs to DB.  

---

## Streamlit Frontend (Optional)
For hackathon demos, add a simple Streamlit app:
```bash
streamlit run app.py
```

This dashboard can:
- View pending customers
- Trigger calls manually
- Display outcomes
- Hear back the generated TTS audio response (`response.wav`)

---

## Tech Stack
- **Python**
- **FastAPI**
- **SQLite**
- **Twilio API**
- **Groq API (TTS + STT + LLM)**
- **Google SpeechRecognition**
- **Streamlit**
- **Ngrok**

---

## Current Limitations
- Not real time **streaming** conversation (batch STT → classify → TTS).  
- Needs paid Twilio + verified caller ID.  
- Uses SQLite (demo only, can be extended to Postgres/MySQL).  

---

## Future Improvements
-  Real time streaming conversation (instead of one shot record/transcribe).  
-  Analytics dashboard for customer responses.  
-  Multilingual support.  
-  Deploy to cloud (AWS/GCP/Azure).  

---

## Hackathon Value
This project shows:
- **Agentic AI workflow**
- **Integration of LLMs with real-world APIs**
- **Voice-based automation for fintech use cases**

Perfect as a **demo-ready prototype** 

---

## Author
Agrim Gupta  
Repo: [Loan-Collection-Agentic-VoiceBot](https://github.com/AgrimGupta04/Loan-Collection-Agentic-VoiceBot)
