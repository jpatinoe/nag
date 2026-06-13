import os
from fastapi import FastAPI, Form
from dotenv import load_dotenv
from parser import parse_task, parse_due_date, merge_followup
from database import setup_database, add_task, list_tasks, mark_done, set_due_date, update_task_name, save_pending_state, get_pending_state, clear_pending_state
from twilio.rest import Client
from datetime import datetime
import threading
from scheduler import check_tasks, morning_digest
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
app = FastAPI()
setup_database()
# Start the scheduler in the background
bg_scheduler = BackgroundScheduler()
bg_scheduler.add_job(check_tasks, 'interval', minutes=30)
bg_scheduler.add_job(morning_digest, 'cron', hour=9, minute=0)
bg_scheduler.start()
print("Scheduler started in background.")

def send_whatsapp(message):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    client.messages.create(
        from_=os.getenv("TWILIO_WHATSAPP_FROM"),
        to=os.getenv("TWILIO_WHATSAPP_TO"),
        body=message
    )

@app.post("/webhook")
async def webhook(Body: str = Form(...), From: str = Form(...)):
    message = Body.strip()
    print(f"Incoming from {From}: {message}")

    # Check if user is in the middle of a follow-up conversation
    pending = get_pending_state(From)

    if pending:
        state, task_id = pending

        # Waiting for a due date
        if state == "awaiting_date":
            print("Parsing date reply...")
            due_parsed = parse_due_date(message)
            set_due_date(task_id, due_parsed)
            clear_pending_state(From)
            send_whatsapp(f"✅ Got it — due {due_parsed}")
            return {"status": "ok"}

        # Waiting for a follow-up answer
        if state.startswith("awaiting_followup:"):
            question = state.replace("awaiting_followup:", "")
            # Get the task name to merge with
            conn_tasks = list_tasks()
            task_name = next((t[1] for t in conn_tasks if t[0] == task_id), None)
            if task_name:
                updated_name = merge_followup(task_name, question, message)
                update_task_name(task_id, updated_name)
                send_whatsapp(f"✅ Updated: {updated_name}")
            clear_pending_state(From)
            return {"status": "ok"}

    # Handle "list" command
    if message.lower() == "list":
        tasks = list_tasks()
        if not tasks:
            send_whatsapp("No pending tasks.")
        else:
            lines = ["📋 Your tasks:\n"]
            for i, t in enumerate(tasks, start=1):
                id, name, urgency, needs_date, due_date, follow_up, last_nudged = t
                date_str = f" | due: {due_date}" if due_date else ""
                lines.append(f"[{i}] ({urgency}) {name}{date_str}")
            send_whatsapp("\n".join(lines))
        return {"status": "ok"}

    # Handle "done all" command
    if message.lower() == "done all":
        tasks = list_tasks()
        for t in tasks:
            mark_done(t[0])
        send_whatsapp(f"✅ All {len(tasks)} tasks marked as done.")
        return {"status": "ok"}

    # Handle "done <number>" command
    if message.lower().startswith("done "):
        try:
            tasks = list_tasks()
            num = int(message.split()[1])
            if 1 <= num <= len(tasks):
                real_id = tasks[num - 1][0]
                mark_done(real_id)
                send_whatsapp(f"✅ Task {num} marked as done.")
            else:
                send_whatsapp(f"No task number {num}.")
        except:
            send_whatsapp("Usage: done <number>")
        return {"status": "ok"}

    # Otherwise treat it as a new task
    print("Parsing task...")
    result = parse_task(message)

    if not result.get("task"):
        send_whatsapp("Hmm, I didn't catch a task there. Try again.")
        return {"status": "ok"}

    task_id = add_task(result)
    task_name = result["task"]

    # If needs a date, ask and save state
    if result["needs_date"]:
        save_pending_state(From, "awaiting_date", task_id)
        send_whatsapp(f"✅ Got it: {task_name}\n📅 When is it due?")

    # If follow-up needed, ask and save state
    elif result["follow_up_question"]:
        save_pending_state(From, f"awaiting_followup:{result['follow_up_question']}", task_id)
        send_whatsapp(f"✅ Got it: {task_name}\n❓ {result['follow_up_question']}")

    # Otherwise just confirm
    else:
        send_whatsapp(f"✅ Saved: {task_name} ({result['urgency']})")

    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "Nag is running"}
