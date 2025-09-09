from groq import Groq
import os 
from database import Database
from dotenv import load_dotenv
load_dotenv()

class Outcome_agent:
    def __init__(self, use_groq = False, api_key=None):
        self.use_groq = use_groq
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key = self.api_key) if self.use_groq else None
        self.db = Database()

    def classify_response(self, transcript: str) -> dict:
        ## To classify the response of the customer from the conversation 
        ## return a dictionary with the status of response + notes

        if not self.use_groq:
            transcript_lower = transcript.lower()

            if any(word in transcript_lower for word in['yes', 'pay', 'sure', 'okay']):
                return {"status": "SUCCESSFUL", "notes": transcript}
            elif any(word in transcript_lower for word in ["no", "can't", "later", "probelm"]):
                return {"status": "NEED FOLLOW UP", "notes": transcript} 
            else:
                return {"status": "FAILED", "notes": transcript}
            

        prompt = f"""You are a classifier of outcome for a loan repayment call reminder.
        Transcript : "{transcript}"
            
        Decide one of:
        - SUCCESSSFUL (customer agrees to pay)
        - NEEDS FOLLOW-UP (customer refuses / delays / unsure)
        - FAILED (irrelevent / no response)
            
        Respond in JSON with keys: status, notes,
        """

        response = self.client.chat.completions.create(
            model = "llama1-8b-8192",
            messages = [{"role": "user", "content": prompt}],
            temperature = 0.2
        )

        try:
            import json 
            result = json.loads(response.choices[0].message["content"])
        except:
            result = {"status": "FAILED", "notes": transcript}

        return result


    def process_customer(self, transcript: str, customer_id: int):
        ## To process what customer was categorized into what outcome.

        outcome = self.classify_response(transcript)
        self.db.log_call_outcome(customer_id, outcome['status'], outcome['notes'])
        return outcome
    

if __name__ == "__main__":
    agent = Outcome_agent(use_groq = True)

    fake_transcript = "Yes, I will make the payment tomorrow."

    db = agent.db
    customers = db.con.execute("SELECT id, name FROM customers WHERE call_status = 'Pending' ")

    if customers:
        c_id, name = customers[0]
        print(f"Processing {name} (ID={c_id}) with transcript: {fake_transcript}")
        outcome = agent.process_customer(fake_transcript, c_id)
        print("Outcome:", outcome)
    else:
        print("No pending customers found.")
        