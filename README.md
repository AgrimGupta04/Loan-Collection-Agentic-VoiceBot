# Loan Collection AI Voice Agent

## Description

This project implements an intelligent AI voice agent designed to proactively contact customers regarding overdue loan payments. The agent reminds customers of their due amount, understands their intent using natural language processing (powered by Groq), orchestrates actions like sending payment links via SMS (using Twilio), and logs outcomes to a database. The core backend is built with FastAPI and designed for real-time, streaming conversations managed by Vapi.ai.

---

## Features 

* **Real-time Voice Calls:** Initiates outbound calls using Vapi.ai for seamless, low-latency conversations.
* **Intent Classification:** Uses Groq's fast LLMs to understand user intent (e.g., agrees to pay, refuses, unclear) in real-time.
* **Conversation Memory:** Maintains a short-term history for each call to provide context during multi-turn interactions.
* **Multi-channel Orchestration:** Intelligently decides when to send an SMS payment link via Twilio during a live voice call based on user intent.
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
* **Deployment:** Railway (using Gunicorn & Uvicorn)
* **Development:** Uvicorn, Ngrok, python-dotenv

---

## Project Structure 

your-project-folder/
├── .env # Your secret keys (DO NOT COMMIT)
├── .env.example # Example environment variables
├── .gitignore # Files ignored by Git
├── .railwayignore # Files ignored by Railway deployment
├── requirements.txt # Project dependencies
├── railway.toml # Railway deployment configuration
├── Procfile # Alternative deployment config (e.g., for Heroku)
├── server.py # Main FastAPI server (orchestrator)
├── app.py # Optional Streamlit developer dashboard
└── src/
    ├── __init__.py
    ├── action_agent.py # Agent responsible for executing actions (SMS)
    ├── database.py # Database interaction logic
    ├── dialogue_agent.py # Core agent logic (intent classification, response generation)
    └── services/
        ├── __init__.py
        ├── mcp_service.py # Twilio API interaction (SMS, Lookup)
        ├── transcription_service.py # Audio transcription for file uploads
        └── vapi_service.py # Vapi API interaction (starting calls)

---

## Setup & Installation 

1. **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd your-project-folder
    ```

2. **Create a Virtual Environment:**
    ```bash
    python -m venv voice-bot-env
    source voice-bot-env/bin/activate  # On Windows use `voice-bot-env\Scripts\activate`
    ```

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables:**
    * Copy the `.env.example` file to `.env`: `cp .env.example .env`
    * Edit the `.env` file and fill in your actual API keys and credentials for Groq, Twilio, and Vapi.

---

## Running Locally 

1. **Run the FastAPI Server:**
    ```bash
    uvicorn server:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

2. **Expose Server with Ngrok (for Vapi Webhook):**
    * Download and install [ngrok](https://ngrok.com/download).
    * Run ngrok in a **separate terminal**:
        ```bash
        ngrok http 8000
        ```
    * Copy the `https://<your-unique-id>.ngrok.io` forwarding URL provided by ngrok.

3. **Configure Vapi Assistant:**
    * Go to your Vapi.ai dashboard.
    * Edit your assistant configuration.
    * Set the **Server URL** to your ngrok forwarding URL + `/webhook/vapi` (e.g., `https://<your-unique-id>.ngrok.io/webhook/vapi`).
    * Paste the **Vapi Prompt** (provided separately) into the assistant's prompt section.
    * Ensure your Vapi Assistant ID is correctly set in your `.env` file (`VAPI_ASSISTANT_ID`).

4. **(Optional) Run Streamlit Dashboard:**
    If you want to use the developer dashboard:
    ```bash
    streamlit run app.py
    ```

---

## API Endpoints 

* `GET /health`: Health check endpoint for deployment monitoring.
* `GET /all-customers`: Retrieves all customers from the database.
* `GET /pending-customers`: Retrieves customers with a 'Pending' status.
* `POST /start-call/{customer_id}`: Triggers an outbound Vapi call to the specified customer.
* `POST /webhook/vapi`: **(Internal)** Webhook endpoint called by Vapi during a live call to get instructions from the `DialogueAgent`.
* `POST /upload-recording/{customer_id}`: Accepts a `.wav` file upload, transcribes it, and processes it through the agent pipeline for testing.

---

## Deployment 

This application is configured for deployment on [Railway](https://railway.app) using the `railway.toml` file. Ensure all necessary environment variables are set in the Railway project settings. The `gunicorn` command in `railway.toml` handles the production serving.

---

## Future Improvements 

* **Sentiment Analysis:** Add a `SentimentAgent` to analyze user tone for more empathetic responses.
* **Pre-call Check:** Implement a `PreflightAgent` using `mcp_service.lookup_number` to validate phone numbers before dialing.
* **Payment Integration:** Connect the SMS link to a real (or mock) payment gateway and add a webhook to update the database status to `PAID`.
* **Enhanced Dialogue:** Improve the `DialogueAgent`'s ability to handle more complex questions and conversational paths.
* **Frontend UI:** Build a React frontend to replace/enhance the Streamlit dashboard for a more polished user experience.
