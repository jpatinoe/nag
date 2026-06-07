import os
from dotenv import load_dotenv
import anthropic
import json
from datetime import datetime

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


def parse_due_date(date_string):
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    Today's date is {today}.
    The user said their task is due: "{date_string}"
    
    Convert this to an ISO format datetime string (YYYY-MM-DD HH:MM:SS).
    If no time is mentioned, assume end of day (23:59:00).
    If the date is ambiguous, make a reasonable assumption.
    
    Return ONLY the datetime string, nothing else. No explanation, no markdown.
    Example output: 2026-06-10 23:59:00
    """
    
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=50,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text.strip()

def merge_followup(task, question, answer):
    prompt = f"""
    A user has a task and you need to update its description based on their answer to a follow-up question.
    
    Task: "{task}"
    Follow-up question that was asked: "{question}"
    User's answer: "{answer}"
    
    Write a single clean task description that naturally incorporates the answer.
    Keep it concise, in the same style as the original task.
    Return ONLY the updated task description, nothing else.
    
    Examples:
    Task: "Call insurance", Question: "Do you have a deadline?", Answer: "not really" -> "Call insurance, no specific deadline"
    Task: "Buy groceries", Question: "Any specific items?", Answer: "milk and eggs" -> "Buy groceries — milk and eggs"
    Task: "Book GP appointment", Question: "Any time preference?", Answer: "morning if possible" -> "Book GP appointment, preferably in the morning"
    """

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()

if __name__ == "__main__":
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