from database import Database 
from outcome_agent import Outcome_agent
from caller_agent import CallerAgent

from pyngrok import ngrok
from pyngrok import conf

# Configure pyngrok to use the manually installed ngrok binary
ngrok_path = "C:/ngrok/ngrok.exe" # Use forward slashes or double backslashes
conf.get_default().ngrok_path = ngrok_path

ngrok.set_auth_token("YOUR_NGROK_AUTH_TOKEN")

public_url = ngrok.connect(8000)
print("Public URL:", public_url)

def run_pipeline():
    db = Database()
    caller = CallerAgent(use_groq = True)
    agent = Outcome_agent(use_groq = False)

    customers = db.fetch_due_customers()

    if not customers:
        print("No pending Customers found!")
        return
    
    for customer in customers:
        c_id, name, phone,  due_date, loan_amount, call_status, notes = customer
        print(f"\nProcessint Time {name} (ID = {c_id}) with loan amount as {loan_amount} due on {due_date}.")

        test_transcript = caller.transcribe_audio("user_says_he_will_pay.wav")

        outcome = agent.process_customer(test_transcript, c_id)
        print("Outcome:", outcome)

        caller.synthesize_speech(f"Hello {name}, we have noted your response as: {outcome['status']}")

def run_twilio_call():
    """
    This will make a real phone call using the Twilios ervice.
    """
    db = Database()
    caller = CallerAgent(use_groq = True)

    customers =  db.fetch_due_customers()
    if not customers:
        print("No pending Customers found!")
        return
    
    c_id, name, phone, due_date, loan_amount, call_status, notes = customers[0]

    print(f"Calling {name} at {phone} for loan amount as {loan_amount} due on {due_date}.") 

    test_number = "+918400601441"

    caller.make_call(
        to_number=test_number,
        message=f"Hello {name}, this is a reminder for your loan payment of amount {loan_amount} due on {due_date}. Please pay as soon as possible. Thank you!"
    )

if __name__ == "__main__":

    # run_pipeline()
    run_twilio_call()