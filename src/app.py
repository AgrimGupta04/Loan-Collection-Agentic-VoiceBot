import streamlit as st
from database import Database
from caller_agent import CallerAgent
from outcome_agent import Outcome_agent
import os

db = Database()
caller = CallerAgent(use_groq=True)
agent = Outcome_agent(use_groq=False)

st.title("Loan Collection VoiceBot Demo")

## Show DB
st.header("Pending Customers in DB")
customers = db.fetch_due_customers()
if customers:
    st.write("These are the customers pending a reminder call:")
    st.table(
        [{"ID": c[0], "Name": c[1], "Phone": c[2], "Due Date": c[3],
          "Loan Amount": c[4], "Status": c[5], "Notes": c[6]} for c in customers]
    )
else:
    st.success("No pending customers in database!")

st.subheader("All Customers (with updated status)")
all_customers = db.con.execute("SELECT * FROM customers").fetchall()
st.table(
    [{"ID": c[0], "Name": c[1], "Phone": c[2], "Due Date": c[3],
      "Loan Amount": c[4], "Status": c[5], "Notes": c[6]} for c in all_customers]
)

## Local Test with Audio File
st.header("Local Pipeline Test (Voice Note → STT → DB Update → TTS)")

uploaded_file = st.file_uploader("Upload a .wav file (simulating customer response)", type=["wav"])

if uploaded_file is not None:
    audio_input = "uploaded_test.wav"
    with open(audio_input, "wb") as f:
        f.write(uploaded_file.getbuffer())

    transcript = caller.transcribe_audio(audio_input)
    st.write(f"**Transcribed Text:** {transcript}")

    if customers:
        customer_id = customers[0][0]  ## Taking first pending customer
        outcome = agent.process_customer(transcript, customer_id)
        st.write("**Outcome Classification:**", outcome)

        ## Generating response speech
        response_text = f"Hello {customers[0][1]}, we have noted your response as: {outcome['status']}."
        response_file = caller.synthesize_speech(response_text)

        if response_file and os.path.exists(response_file):
            st.audio(response_file, format="audio/wav")
            st.success("Response audio generated and played below.")
    else:
        st.warning("No customers in DB to attach this response to.")

## Twilio Call
st.header("Trigger Real Twilio Call")

if customers:
    selected_customer = customers[0]  # Just take first for demo
    c_id, name, phone, due_date, loan_amount, call_status, notes = selected_customer
    st.write(f"Ready to call **{name}** at **{phone}** about due amount **₹{loan_amount}** on **{due_date}**")

    if st.button("Make Twilio Call"):
        call_sid = caller.make_call(
            to_number=phone,
            message=f"Hello {name}, this is a reminder for your loan payment of amount {loan_amount} due on {due_date}. Please pay as soon as possible. Thank you!"
        )
        if call_sid:
            st.success(f"Call initiated! Twilio Call SID: {call_sid}")
        else:
            st.error("Failed to initiate call. Check Twilio config.")
else:
    st.info("No customers available to call.")
