import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from database import setup_database, list_tasks
from datetime import datetime, timedelta
from twilio.rest import Client

load_dotenv()

scheduler = BlockingScheduler()

def send_whatsapp(message):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    client.messages.create(
        from_=os.getenv("TWILIO_WHATSAPP_FROM"),
        to=os.getenv("TWILIO_WHATSAPP_TO"),
        body=message
    )

def check_tasks():
    print(f"\n🔍 Checking tasks... ({datetime.now().strftime('%H:%M:%S')})")
    tasks = list_tasks()

    if not tasks:
        print("No pending tasks.")
        return

    now = datetime.now()

    for task in tasks:
        id, name, urgency, needs_date, due_date, follow_up = task

        # Tasks with no due date
        if not due_date:
            if urgency == "high":
                msg = f"🔴 Hey, don't forget: {name}"
                print(msg)
                send_whatsapp(msg)
            continue

        # Try to parse the due date
        try:
            due = datetime.fromisoformat(due_date)
        except:
            print(f"📅 {name} — due: {due_date} ({urgency})")
            continue

        time_left = due - now

        if time_left < timedelta(0):
            msg = f"⚠️ Nag: OVERDUE — {name}"
            print(msg)
            send_whatsapp(msg)
        elif time_left < timedelta(hours=2):
            msg = f"🔴 Nag: Due very soon — {name}"
            print(msg)
            send_whatsapp(msg)
        elif time_left < timedelta(hours=24):
            msg = f"🟡 Nag: Due today — {name}"
            print(msg)
            send_whatsapp(msg)
        elif time_left < timedelta(days=3):
            msg = f"🟢 Nag: Coming up — {name}"
            print(msg)
            send_whatsapp(msg)

@scheduler.scheduled_job('interval', minutes=1)
def scheduled_check():
    check_tasks()

if __name__ == "__main__":
    setup_database()
    print("🔔 Nag scheduler running. Press Ctrl+C to stop.")
    print("Checking tasks every minute...\n")
    check_tasks()  # Run once immediately on start
    scheduler.start()