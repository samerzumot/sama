"""
STEP 1 — CREATE SESSION
Run this first. It creates the Tavus conversation and gives you a URL to send to your student.
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TAVUS_API_KEY")
BASE_URL = "https://tavusapi.com"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# EQ-eliciting system prompt — designed to surface self-awareness,
# regulation, empathy, and motivation signals naturally
EQ_PROMPT = """
You are a warm but honest college admissions counselor named Alex.
Your job is to help the student reflect on their college application journey.

During this conversation, naturally weave in the following types of questions
to surface authentic emotional responses. Do NOT make it feel like a test.

1. Ask them about a moment their application or grades didn't go as planned.
   How did they handle it? Let them sit with the answer.

2. Ask what they genuinely want from college — not what sounds good, what they actually want.
   Push back gently if the answer feels rehearsed.

3. Ask if there's something about themselves they find hard to put into their application.
   Give them space to be honest.

4. Toward the end, ask: "If you don't get into your top choice, what's your plan?"
   Note how they respond emotionally, not just logistically.

Keep the conversation to 15-20 minutes. Be present, listen actively, and reflect
back what you hear. The goal is a real conversation, not an interview.
"""

def create_session():
    payload = {
        "replica_id": "rfe12d8b9597",   # Nathan — Bookshelf
        "persona_id":  "pdac61133ac5",    # Interviewer persona, we override with our context below
        "conversation_name": "EQ College Prep Session",
        "conversational_context": EQ_PROMPT,
        "properties": {
            "max_call_duration": 1800,          # 30 min hard cap
            "participant_left_timeout": 60,
            "enable_recording": True
        }
    }

    print("Creating session...")
    r = requests.post(f"{BASE_URL}/v2/conversations", headers=HEADERS, json=payload)

    if r.status_code != 200:
        print(f"Error {r.status_code}: {r.text}")
        return

    data = r.json()
    conversation_id  = data.get("conversation_id")
    conversation_url = data.get("conversation_url")

    print("\n" + "="*60)
    print("SESSION CREATED")
    print("="*60)
    print(f"Conversation ID : {conversation_id}")
    print(f"\nSend this URL to your student:")
    print(f"\n  {conversation_url}\n")
    print("="*60)
    print("Save the Conversation ID — you need it for step 2.")
    print("="*60 + "\n")

    # Save to file so step 2 can pick it up automatically
    with open("session_id.txt", "w") as f:
        f.write(conversation_id)

    print("session_id.txt saved. Run eq_score.py when the session ends.\n")

if __name__ == "__main__":
    create_session()