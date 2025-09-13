from database import Database
from outcome_agent import Outcome_agent
from twilio.rest import Client
from groq import Groq
import speech_recognition as sr

import os 
from dotenv import load_dotenv
load_dotenv()

class CallerAgent:
    def __init__(self, use_groq=True, api_key=None):
        self.use_groq = use_groq
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = Groq(api_key=self.api_key) if self.use_groq else None
        self.recognizer = sr.Recognizer()

        ## Twilio integration can be added here for real calls
        self.twilio_sid = os.getenv("TWILIO_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_client = Client(self.twilio_sid, self.twilio_auth_token)
    

    def transcribe_audio(self, audio_file: str) -> str:
        """Using Google STT to transcribe audio file to text."""

        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                transcript = self.recognizer.recognize_google(audio_data)
                return transcript
        except sr.UnknownValueError:
            return "[Unintelligible audio]"
        except sr.RequestError as e:
            return f"[Google API error: {e}]"


    def synthesize_speech(self, text: str, output_file: str = "response.wav"):
        """
        Convert text to speech using Groq TTS.
        """
        
        if not self.use_groq or not self.client:
            print(f"(Mock TTS) Would generate {output_file} with text: {text}")
            return output_file

        try:
            response = self.client.audio.speech.create(
                model = 'playai-tts',
                voice = 'Chip-PlayAI',
                input = text,
                response_format = "wav" 
            )

            response.write_to_file(output_file)

            print(f"(Groq TTS) will generate {output_file} with text: {text}")
            return output_file
        except Exception as e:
            print("Groq TTS error:", e)
            return None
        

    def make_call(self, to_number: str, message: str):
        """Make a call using Twilio and response with the generated response."""
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.twilio_number,
                twiml=f'<Response><Say>{message}</Say></Response>'
            )
            print(f"Call initiated with SID: {call.sid}")
            return call.sid
        except Exception as e:
            print("Twilio call error:", e)
            return None
        
    def simulate_conversation(self, audio_input: str):
        transcript = self.transcribe_audio(audio_input)
        print(f"Customer said: {transcript}")

        ## Note -> Later OutcomeAgent generates this output
        response_text = "Thank you, I will update your payment info."
        self.synthesize_speech(response_text)

        return transcript, response_text
    

if __name__ == "__main__":
    caller = CallerAgent()
    audio_file = "user_says_he_will_pay.wav"
    transcript, reply = caller.simulate_conversation(audio_file)

    print("Transcript:", transcript)
    print("Reply:", reply)