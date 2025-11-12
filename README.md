# Loan Collection AI Voice Agent

## Description

This project implements an intelligent AI voice agent designed to proactively contact customers regarding overdue loan payments. The agent reminds customers of their due amount, understands their intent using natural language processing (powered by Groq), orchestrates actions like sending payment links via SMS (using Twilio), and logs outcomes to a database. The core backend is built with FastAPI and designed for real-time, streaming conversations managed by Vapi.ai.

---

## Features 

* **Real-time Voice Calls:** Initiates outbound calls with low-latency, human-like conversation using Vapi.ai.
* **Real-time Intent Classification:** Leverages Groq's high-speed LLM inference to understand user intent (e.g., "agrees to pay," "refuses," "needs help") instantly.
* **Conversation Memory:** Maintains a short-term history for each call to provide context during multi-turn interactions.
* **Multi agent Orchestration:** Uses a backend agentic (MCP) pipeline to manage dialogue, sentiment, and actions.
* **Batch Audio Processing:** Includes an endpoint for uploading `.wav` files for testing the transcription and agent logic without making live calls.
* **Database Integration:** Uses SQLite to store customer data and log call outcomes.
* **Asynchronous Backend:** Built with FastAPI for high performance and scalability.

---

## Tech Stack 

* **Backend:** Python, FastAPI
* **AI/LLM:** Groq (for fast inference)
* **Voice/Telephony:** Vapi.ai (for call management & streaming STT/TTS)
* **SMS/Lookup:** Twilio
* **Database:** SQLite
* **STT (for batch):** Google Web Speech API via `SpeechRecognition` library
* **Deployment:** Render

---

## Project Structure 

```
your-project-folder/
├── Frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── endpoints.js         # Defines frontend API call functions
│   │   ├── assets/                # Images, icons, etc.
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── footer.jsx
│   │   │   │   └── header.jsx
│   │   │   ├── core/
│   │   │   │   ├── addCustomer.jsx
│   │   │   │   ├── makeCall.jsx
│   │   │   │   └── uploadFile.jsx
│   │   │   ├── about.jsx
│   │   │   ├── heroSection.jsx
│   │   │   ├── scrollToTop.jsx
│   │   │   └── pages/               # Page components (e.g., Home, Dashboard)
│   │   │
│   │   ├── App.css
│   │   ├── App.jsx                # Main React app component
│   │   ├── index.css
│   │   └── main.jsx               # React entry point
│   │
│   ├── .env
│   ├── .gitignore
│   ├── eslint.config.js
|   ├── package-lock.json
|   ├── pachage.json
|   ├── vite.config.js
│   └── index.html
│
│
├── src/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── mcp_service.py         # Handles Twilio SMS/Lookup
│   │   ├── transcription_service.py # Handles audio transcription
│   │   └── vapi_service.py        # Handles Vapi.ai API calls
│   │
│   ├── __init__.py
│   ├── action_agent.py        # Logic for executing actions (e.g., send SMS)
│   ├── database.py            # Manages SQLite database connection and queries
│   ├── dialogue_agent.py      # Core LLM logic for intent and response
│   └── sentiment_agent.py     # Logic for sentiment analysis
│
├── demo_output/
|   ├── user_says_he_will_not_pay.wav
│   └── user_says_he_will_pay.wav
│
├── .gitignore
├── .railwayignore
├── procfile                 # Defines processes for PaaS (e.g., Railway, Heroku)
├── railway.toml             # Railway deployment configuration
├── README.md
├── requirements.txt         # Python backend dependencies
└── server.py                # Main FastAPI application (API endpoints, webhooks)
```
---

## Setup & Installation 
You can try the hosted version here:  
🔗 **Live Frontend:** [https://loan-collection-agentic-voicebot-frontend.onrender.com](https://loan-collection-agentic-voicebot-frontend.onrender.com)

If you’d like to run this project locally for development or testing, follow the steps below.

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/AgrimGupta04/Loan-Collection-Agentic-VoiceBot.git
    cd Loan-Collection-Agentic-VoiceBot
    ```

2. **Create a Virtual Environment:**
# Windows
    python -m venv venv
    .\venv\Scripts\activate
    

# macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables:**
    # .env

    # Vapi.ai (for voice calls)
    VAPI_API_KEY=sk_...
    VAPI_ASSISTANT_ID=asst_...
    VAPI_PHONE_NUMBER_ID=pn_...

    # Twilio (for SMS and number lookup)
    TWILIO_ACCOUNT_SID=AC...
    TWILIO_AUTH_TOKEN=...
    TWILIO_PHONE_NUMBER=+1...

    # Groq (for fast LLM inference)
    GROQ_API_KEY=gsk_...

---

## Running Locally 

1. **Run the FastAPI Server:**
    ```bash
    uvicorn server:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

2. **Fronetend:**

    * # From the root folder 
        ```bash
        cd Frontend
        npm install
        ```

        Set up environment variables

        Create a file named .env in the /Frontend directory:

        If running locally:
        ```bash
        # /Frontend/.env
        VITE_API_BASE_URL=http://127.0.0.1:8000
        # /Frontend/.env        ## If your backend is deployed (for example, on Railway or Render):
        VITE_API_BASE_URL=http://127.0.0.1:8000
        # Run the frontend app locally
        npm run dev
        ```

3. **(Required for Vapi) Expose Your Local Server:**

    * If you’re testing locally, Vapi.ai needs to send webhooks to your local server.
    * You must expose your port 8000 to the internet using a tool like ngrok.

    ngrok http 8000
   


4. **Configure Vapi Assistant:**
    * Go to your Vapi.ai dashboard.
    * Edit your assistant configuration.
    * Set the **Server URL** to your ngrok forwarding URL + `/webhook/vapi` (e.g., `https://<your-unique-id>.ngrok.io/webhook/vapi`).
    * Paste the **Vapi Prompt** (provided separately) into the assistant's prompt section.
    * Ensure your Vapi Assistant ID is correctly set in your `.env` file (`VAPI_ASSISTANT_ID`).

---

## API Endpoints 

* `GET /health`: Health check endpoint for deployment monitoring.
* `GET /all-customers`: Retrieves all customers from the database.
* `GET /pending-customers`: Retrieves customers with a 'Pending' status.
* `POST /start-call/{customer_id}`: Triggers an outbound Vapi call to the specified customer.
* `POST /webhook/vapi`: **(Internal)** Webhook endpoint called by Vapi during a live call to get instructions from the `DialogueAgent`.
* `POST /upload-recording/{customer_id}`: Accepts a `.wav` file upload, transcribes it, and processes it through the agent pipeline for testing.

---

## Future Improvements 

* **Payment Integration:** Connect the SMS link to a real (or mock) payment gateway and add a webhook to update the database status to `PAID`.
* **Enhanced Dialogue:** Improve the `DialogueAgent`'s ability to handle more complex questions and conversational paths.
