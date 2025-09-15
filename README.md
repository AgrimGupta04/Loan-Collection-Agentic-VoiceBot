# Loan Reminder Voice Bot 

## Overview
This project is an **AI-powered voice bot** that reminds customers about their **Loan Payments** via automated calls.  
It integrates:
- **Google Speech-to-Text (STT)** → transcribes customer responses.  
- **Groq Text-to-Speech (TTS)** → generates natural speech responses.  
- **Twilio** → handles phone call automation.  
- **SQLite** → stores customer data and call outcomes.  
- **FastAPI + Ngrok** → exposes endpoints for Twilio to interact with.  

The bot calls customers, plays reminders, records responses, classifies them (e.g., *SUCCESSFUL, NEED FOLLOW-UP, FAILED*), and logs outcomes in the database.

---

## Features
- Convert speech ↔ text (Google STT + Groq TTS).
- Automated customer calls with Twilio.
- SQLite database for customer records.
- Outcome classification using keyword-based rules or Groq LLM.
- FastAPI + Ngrok integration for Twilio webhooks.

---

## Folder Structure
```
src/
│── database.py        # Handles SQLite database
│── caller_agent.py    # Handles STT + TTS + Twilio call logic
│── outcome_agent.py   # Classifies customer responses
│── mcp_integration.py # FastAPI server for Twilio webhook integration
│── main.py            # Orchestration script for testing pipeline
│── requirements.txt   # Dependencies
│── .env               # API keys and credentials
```

---

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/loan-reminder-bot.git
cd loan-reminder-bot/src
```

### 2. Create a virtual environment
```bash
python -m venv voice-bot-env
source voice-bot-env/bin/activate   # On Linux/Mac
voice-bot-env\Scripts\activate   # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Variables
Create a **.env** file inside `src/` and add:

```ini
# Groq API
GROQ_API_KEY=your_groq_api_key

# Twilio
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_registered_number

# Ngrok
NGROK_AUTH_TOKEN=your_ngrok_auth_token
```

---

## Running the Project

### 1. Initialize database
```bash
python database.py
```
This will seed customers into the database.

### 2. Run FastAPI server
```bash
uvicorn mcp_integration:app --reload --port 8000
```

### 3. Start Ngrok tunnel
```bash
ngrok http 8000
```
Copy the generated public URL and set it in Twilio **Voice Webhook URL**.

### 4. Run main script
```bash
python main.py
```
- `run_pipeline()` → simulates flow using local audio.  
- `run_twilio_call()` → triggers an actual call using Twilio.

---

## Demo Plan
1. Run the FastAPI server + Ngrok.  
2. Configure Twilio webhook with Ngrok public URL.  
3. Use `main.py` to make a test call.  
4. Customer replies → Twilio records response → Google STT transcribes → Groq classifies → Database updated.  

---

## Tech Stack
- **Python**
- **FastAPI**
- **SQLite**
- **Twilio API**
- **Groq API (TTS + STT + LLM)**
- **Google SpeechRecognition**
- **Ngrok**

---

## Future Improvements
-  Real-time streaming conversation (instead of one-shot record/transcribe).  
-  Analytics dashboard for customer responses.  
-  Multilingual support.  
-  Deploy to cloud (AWS/GCP/Azure).  

---

## Author
Built by Agrim Gupta
