# from json import load
# import speech_recognition as sr
from groq import Groq, GroqError
import os 
from dotenv import load_dotenv

load_dotenv()

# recognizer = sr.Recognizer()

# def transcribe_audio_file(file_path: str) -> str:
#     """
#     Transcribes an audio file (.wav) to text using Google's free web API.

#     Args:
#         file_path (str): The local path to the audio file.

#     Returns:
#         str: The transcribed text, or an error message if transcription fails.
#     """

#     if not file_path:
#         print("TranscriptionService: No file path provided.")
#         return "[ERROR: No file path provided]"

#     print(f"TranscriptionService: Processing file at {file_path}...")

#     try:
#         with sr.AudioFile(file_path) as source:
#             audio_data = recognizer.record(source)
#             # Recognize speech using Google's web API
#             transcript = recognizer.recognize_google(audio_data)
#
#             print(f"TranscriptionService: Success -> '{transcript}'")
#             return transcript
    
#     except sr.UnknownValueError:
#         # This error is raised when the API can't understand the audio
#         print("TranscriptionService: Google Speech Recognition could not understand the audio.")
#         return "[Unintelligible audio]"
#     except sr.RequestError as e:
#         # This error is raised for API-level issues
#         print(f"TranscriptionService: Could not request results from Google API, {e}")
#         return f"[Google API error: {e}]"
#     except Exception as e:
#         print(f"TranscriptionService: An unexpected error occurred {e}")
#         return f"[Transcription failed: {e}]"


def transcribe_audio_file(file_path: str, api_key = None) -> str:
    """
     Transcribes an audio file (.wav) to text using Google's free web API.

    Args:
        file_path (str): The local path to the audio file.
        api_key (str, optional): The API key for authentication.

    Returns:
         str: The transcribed text, or an error message if transcription fails.
     """
    
    if not file_path:
        print("Transcription Service: No file path provided.")
        return "[ERROR: No file path provided]"
    
    api_key = api_key or os.getenv("GROQ_API_KEY")
        
    if not api_key:
        raise ValueError("Groq API key not provided.")

    try:
        client = Groq(api_key=api_key)
        print("Transcription Service: Initiated Groq Client.")
        print(f"TranscriptionService: Processing file at {file_path} using Whisper.")

        with open(file_path, 'rb') as audio_file:
            ## Calling groq model for transcription

            transcription = client.audio.transcriptions.create(
                model = "whisper-large-v3",
                file = audio_file,
                response_format = "text"
            )
        
        result = str(transcription)

        print(f"Transcription Service: Success -> '{result[:100]}'")
        return result

    except GroqError as e:
        print(f"Transcription Service: Groq API error during transcription: {e}")
        return f"[Groq API error: {e.status_code} - {e.message}]"
    
    except Exception as e:
        print(f"Transcription Service: An unexpected error occurred: {e}")
        return f"[Transcription failed: {e}]"