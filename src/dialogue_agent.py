from groq import Groq
import os 
from dotenv import load_dotenv
import json
load_dotenv()

class Dialogue_agent:
    """ 
    This is the  intelligent core of the voice bot. It decides what to do next in a conversation.
    This Agent is stateless, it doesn't manage the call or the database.
    """
    def __init__(self, use_groq = True, api_key=None):
        self.use_groq = use_groq
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key = self.api_key) if self.use_groq else None

    def _classify_intent(self, transcript: str, conversation_history: list = None) -> dict:
        """
        To classify the intent of the customer from the conversation and history
        return a dictionary with the intent of response 
        """

        if not self.use_groq:
            transcript_lower = transcript.lower()

            if any(word in transcript_lower for word in['yes', 'pay', 'sure', 'okay']):
                return {"intent": "AGREES_TO_PAY"}
            elif any(word in transcript_lower for word in ["no", "can't", "later", "problem"]):
                return {"intent": "REFUSES_TO_PAY"}
            else:
                return {"intent": "UNCLEAR"}
            

        history_prompt = ""
        if conversation_history:
            history_text = "\n".join(conversation_history)
            history_prompt = f"Consider the following conversation history:\n{history_text}\n\n"

        prompt = f"""{history_prompt}Analyze the user's intent from the *latest user message* below, considering the full conversation context.
        Transcript : "{transcript}"
            
        Decide among one of the classes of the following JSON keys:
        - "AGREES_TO_PAY": User agrees to pay their loan.
        - "REFUSES_TO_PAY": User explicitly refuses to pay or states they cannot.
        - "REQUESTS_INFO": User asks for more details about the loan or payment.
        - "END_CONVERSATION": User wants to end the call.
        - "UNCLEAR": The user's intent is not clear.

        Respond with only a single JSON object contianing the key "intent".
        Example: {{"intent: AGREES_TO_PAY"}}
        """

        try:
            response = self.client.chat.completions.create(
                model = "llama3-8b-8192",
                messages = [{"role": "user", "content": prompt}],
                temperature = 0.0,
                response_format = {"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return {"intent": "UNCLEAR"}

    def get_next_action(self, last_transcript: str, customer_data: dict, conversation_history: list = None) -> dict:
        """
        This is the main public method. It decides the next action for the orchestrator.
        
        Args:
            last_transcript: The latest thing the user said.
            customer_data: A dict with info like {'name': 'John Doe', 'loan_amount': 5000}.
            conversation_history (list, optional): A list of past user and agent conversation.

        Returns:
            A dictionary representing the action to be taken.
        """
        customer_name = customer_data.get("name", "there")
        loan_amount = customer_data.get("loan_amount", "your amount")

        # 1. Understand the user's intent
        classification = self._classify_intent(last_transcript, conversation_history)
        intent = classification.get("intent", "UNCLEAR")
        
        # 2. Decide on an action based on the intent
        if intent == "AGREES_TO_PAY":
            # This is a multi-action response: reply and then send an SMS.
            # The server will handle executing these in order.
            action_plan =  {
                "action": "SEQUENCE",
                "payload": [
                    {
                        "type": "REPLY",
                        "text": f"Excellent. Thank you, {customer_name}. To make it easy, I am sending a secure payment link to your phone right now."
                    },
                    {
                        "type": "SEND_SMS",
                        "message": f"Hello {customer_name}, here is your link to pay the outstanding amount of ${loan_amount}. Link: https://your-secure-link.com/pay"
                    },
                    {
                        "type": "END_CALL",
                        "text": "The link has been sent. Thank you for your time. Goodbye."
                    }
                ]
            }
        
        elif intent == "REFUSES_TO_PAY":
            action_plan = {
                "action": "END_CALL",
                "payload": {
                    "text": f"I understand. We've made a note of your response. Thank you for your time, {customer_name}. Goodbye."
                }
            }

        else: # Unclear or any other case
            action_plan = {
                "action": "REPLY",
                "payload": {
                    "text": "I'm sorry, I didn't quite catch that. Could you please repeat it?"
                }
            }

        action_plan["intent"] = intent
        return action_plan
        