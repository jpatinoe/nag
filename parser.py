import os
from dotenv import load_dotenv
import anthropic
import json

# Load the API key from .env file
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def parse_task(user_message):
    prompt = f"""
    You are a task parsing assistant. The user will send you a casual message and you need to extract task information from it.

    Return ONLY a JSON object with these fields:
    - task: a clean description of what needs to be done
    - needs_date: true if the task requires a specific date/time to be useful, false if it's just something to remember
    - urgency: "low", "medium", or "high"
    - follow_up_question: if you need more information to be useful, write a short question here. Otherwise null.

    User message: "{user_message}"

    Return only the JSON, no explanation, no markdown.
    """

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=300,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]  # grab what's between the fences
        if raw.startswith("json"):
            raw = raw[4:]  # remove the word "json" if present
    return json.loads(raw.strip())


# Test it with a few realistic messages
test_messages = [
    "buy milk",
    "dentist appointment sometime next week",
    "remember I need to call mum",
    "meeting with supervisors",
    "pay rent on the 1st"
]

for msg in test_messages:
    print(f"\nInput: '{msg}'")
    result = parse_task(msg)
    print(f"Output: {result}")