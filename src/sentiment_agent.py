import os
import json
from unittest import result
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class Sentiment_agent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        print(f"Sentiment Agent initiated.")

    def analyze_(self, transcript: str) -> str:
        """
        Analyzes the sentiment of a given text using Groq.

        Args:
            transcript (str): The user's speech transcript.

        Returns:
            str: The detected sentiment ("POSITIVE", "NEGATIVE", "NEUTRAL").
                 Defaults to "NEUTRAL" if analysis fails.
        """

        if not self.client or not transcript:
            return "NEUTRAL" 
        
        prompt = f"""Analyze the sentiment of the following user statement from a customer service call.
        Respond ONLY with one word: POSITIVE, NEGATIVE, or NEUTRAL.

        Statement: "{transcript}"

        Sentiment:"""

        try:
            print(f"Sentiment Agent: Analyzing transcript: '{transcript[:50]}")
            response = self.client.chat.completions.create(
                model = "gemma2-9b-it",
                messages = [{"role": "user", "content": prompt}],
                temperature = 0.1,
                max_tokens = 10
            )

            result_text = response.choices[0].message.content.strip().upper()

            if result_text in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
                print(f"Sentiment Agent: Detected sentiment: {result_text}")
                return result_text
            else:
                print(f"Sentiment Agent: Unexpected sentiment result: {result_text}")
                return "NEUTRAL"

        except Exception as e:
            print(f"Sentiment Agent: Error during sentiment analysis: {e}")
            return "NEUTRAL"
