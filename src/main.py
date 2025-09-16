from database import Database
from outcome_agent import Outcome_agent
from caller_agent import CallerAgent

def run_pipeline():
    db = Database()
    caller = CallerAgent(use_groq=True)
    agent = Outcome_agent(use_groq=False)

    customers = db.fetch_due_customers()
    if not customers:
        print("No pending customers found.")
        return

    for c_id, name, phone, due_date, loan_amount, call_status, notes in customers:
        print(f"\n[Pipeline] Processing {name}, due {due_date}, amount {loan_amount}")

        transcript = caller.transcribe_audio("user_says_he_will_pay.wav")
        outcome = agent.process_customer(transcript, c_id)
        print("Outcome:", outcome)

        caller.synthesize_speech(f"Hello {name}, we have noted your response as: {outcome['status']}")

if __name__ == "__main__":
    run_pipeline()
