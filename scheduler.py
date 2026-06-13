import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from database import setup_database, list_tasks, update_last_nudged
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

def get_nudge_interval(time_left, urgency):
    """Return how long to wait between nudges based on time left and urgency."""

    if time_left is None:
        # No due date — use urgency only
        intervals = {
            "high": timedelta(days=1),
            "medium": timedelta(days=3),
            "low": timedelta(weeks=1)
        }
        return intervals.get(urgency, timedelta(days=3))

    if time_left < timedelta(0):
        # Overdue — nudge once then stop
        return None

    elif time_left < timedelta(hours=2):
        # Due very soon — every 30 minutes
        return timedelta(minutes=30)

    elif time_left < timedelta(hours=24):
        # Due today — twice a day (every 6 hours is fine)
        return timedelta(hours=6)

    elif time_left < timedelta(days=3):
        # Due in 1-3 days — twice a day
        return timedelta(hours=12)

    elif time_left < timedelta(days=7):
        # Due in 3-7 days — once a day
        return timedelta(days=1)

    else:
        # More than 7 days away — no nudge yet
        return None

def should_nudge(last_nudged, interval):
    """Check if enough time has passed since last nudge."""
    if interval is None:
        return False
    if not last_nudged:
        return True
    last = datetime.fromisoformat(last_nudged)
    return datetime.now() - last >= interval

def check_tasks():
    print(f"\n🔍 Checking tasks... ({datetime.now().strftime('%H:%M:%S')})")
    tasks = list_tasks()

    if not tasks:
        print("No pending tasks.")
        return

    now = datetime.now()
    nudges_sent = 0

    for task in tasks:
        id, name, urgency, needs_date, due_date, follow_up, last_nudged = task

        # Calculate time left
        time_left = None
        if due_date:
            try:
                due = datetime.fromisoformat(due_date)
                time_left = due - now
            except:
                pass

        # Handle overdue — nudge once then stop
        if time_left is not None and time_left < timedelta(0):
            if not last_nudged:
                msg = f"⚠️ Nag: OVERDUE — {name}"
                print(msg)
                send_whatsapp(msg)
                update_last_nudged(id)
                nudges_sent += 1
            else:
                print(f"⏭️  Skipping overdue '{name}' — already nudged")
            continue

        # Get interval and check if we should nudge
        interval = get_nudge_interval(time_left, urgency)

        if not should_nudge(last_nudged, interval):
            print(f"⏳ Skipping '{name}' — nudged recently")
            continue

        # Build the message
        if time_left is None:
            if urgency == "high":
                msg = f"🔴 Nag: Don't forget — {name}"
            elif urgency == "medium":
                msg = f"🟡 Nag: Reminder — {name}"
            else:
                msg = f"🟢 Nag: When you get a chance — {name}"

        elif time_left < timedelta(hours=2):
            minutes = int(time_left.total_seconds() / 60)
            msg = f"🔴 Nag: Due in {minutes} minutes — {name}"

        elif time_left < timedelta(hours=24):
            hours = int(time_left.total_seconds() / 3600)
            msg = f"🟡 Nag: Due in {hours} hours — {name}"

        elif time_left < timedelta(days=3):
            days = time_left.days
            msg = f"🟠 Nag: Due in {days} days — {name}"

        else:
            days = time_left.days
            msg = f"🟢 Nag: Coming up in {days} days — {name}"

        print(msg)
        send_whatsapp(msg)
        update_last_nudged(id)
        nudges_sent += 1

    print(f"Nudges sent: {nudges_sent}")

def morning_digest():
    """Send a single morning summary of today's tasks and overdue items."""
    print(f"\n☀️  Morning digest ({datetime.now().strftime('%H:%M:%S')})")
    tasks = list_tasks()

    if not tasks:
        return

    now = datetime.now()
    due_today = []
    overdue = []
    no_date_high = []

    for task in tasks:
        id, name, urgency, needs_date, due_date, follow_up, last_nudged = task

        if due_date:
            try:
                due = datetime.fromisoformat(due_date)
                time_left = due - now
                if time_left < timedelta(0):
                    overdue.append(name)
                elif time_left < timedelta(hours=24):
                    due_today.append(name)
            except:
                pass
        elif urgency == "high":
            no_date_high.append(name)

    if not due_today and not overdue and not no_date_high:
        return

    lines = ["☀️ Good morning! Here's your Nag digest:\n"]

    if overdue:
        lines.append("⚠️ Overdue:")
        for t in overdue:
            lines.append(f"  • {t}")

    if due_today:
        lines.append("\n📅 Due today:")
        for t in due_today:
            lines.append(f"  • {t}")

    if no_date_high:
        lines.append("\n🔴 High priority (no date):")
        for t in no_date_high:
            lines.append(f"  • {t}")

    msg = "\n".join(lines)
    print(msg)
    send_whatsapp(msg)

@scheduler.scheduled_job('interval', minutes=30)
def scheduled_check():
    check_tasks()

@scheduler.scheduled_job('cron', hour=9, minute=0)
def scheduled_digest():
    morning_digest()


def test_nudge_logic():
    """Simulate different task scenarios to verify nudge logic."""
    from database import get_connection
    
    print("\n🧪 Running nudge logic tests...\n")
    
    now = datetime.now()
    
    test_cases = [
        {
            "name": "Buy milk (no date, low urgency)",
            "urgency": "low",
            "due_date": None,
            "last_nudged": None
        },
        {
            "name": "Call doctor (no date, high urgency)",
            "urgency": "high",
            "due_date": None,
            "last_nudged": None
        },
        {
            "name": "Submit report (due in 10 days)",
            "urgency": "medium",
            "due_date": (now + timedelta(days=10)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Pay rent (due in 5 days)",
            "urgency": "high",
            "due_date": (now + timedelta(days=5)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Dentist appointment (due in 2 days)",
            "urgency": "medium",
            "due_date": (now + timedelta(days=2)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Pick up prescription (due in 3 hours)",
            "urgency": "high",
            "due_date": (now + timedelta(hours=3)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Zoom call (due in 45 minutes)",
            "urgency": "high",
            "due_date": (now + timedelta(minutes=45)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Send email (overdue by 2 hours)",
            "urgency": "medium",
            "due_date": (now - timedelta(hours=2)).isoformat(),
            "last_nudged": None
        },
        {
            "name": "Clean apartment (nudged 10 mins ago, due in 5 days)",
            "urgency": "medium",
            "due_date": (now + timedelta(days=5)).isoformat(),
            "last_nudged": (now - timedelta(minutes=10)).isoformat()
        },
    ]

    for case in test_cases:
        name = case["name"]
        urgency = case["urgency"]
        due_date = case["due_date"]
        last_nudged = case["last_nudged"]

        time_left = None
        if due_date:
            due = datetime.fromisoformat(due_date)
            time_left = due - now

        interval = get_nudge_interval(time_left, urgency)
        nudge = should_nudge(last_nudged, interval)

        # Simulate the message
        if time_left is not None and time_left < timedelta(0):
            msg = f"⚠️ OVERDUE — {name}"
        elif time_left is None:
            msg = f"📌 No date — {name} ({urgency})"
        elif time_left < timedelta(hours=2):
            minutes = int(time_left.total_seconds() / 60)
            msg = f"🔴 Due in {minutes} minutes — {name}"
        elif time_left < timedelta(hours=24):
            hours = int(time_left.total_seconds() / 3600)
            msg = f"🟡 Due in {hours} hours — {name}"
        elif time_left < timedelta(days=3):
            msg = f"🟠 Due in {time_left.days} days — {name}"
        else:
            msg = f"🟢 Coming up in {time_left.days} days — {name}"

        status = "✅ WOULD NUDGE" if nudge else "⏳ SKIP"
        print(f"{status} | {msg}")
        if interval:
            print(f"         Interval: every {interval}")
        else:
            print(f"         Interval: None (too far / overdue)")
        print()


if __name__ == "__main__":
    import sys
    setup_database()

    if "--test" in sys.argv:
        test_nudge_logic()
    else:
        print("🔔 Nag scheduler running. Press Ctrl+C to stop.")
        print("Checking tasks every 30 minutes. Morning digest at 9am.\n")
        check_tasks()
        scheduler.start()