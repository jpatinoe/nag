from apscheduler.schedulers.blocking import BlockingScheduler
from database import setup_database, list_tasks, mark_done
from datetime import datetime, timedelta

scheduler = BlockingScheduler()

def check_tasks():
    print(f"\n🔍 Checking tasks... ({datetime.now().strftime('%H:%M:%S')})")
    tasks = list_tasks()
    
    if not tasks:
        print("No pending tasks.")
        return
    
    now = datetime.now()
    
    for task in tasks:
        id, name, urgency, needs_date, due_date, follow_up = task
        
        # Tasks with no due date — just surface them as a gentle reminder
        if not due_date:
            if urgency == "high":
                print(f"🔴 Hey, don't forget: {name}")
            elif urgency == "medium":
                print(f"🟡 Reminder: {name}")
            continue
        
        # Try to parse the due date
        try:
            due = datetime.fromisoformat(due_date)
        except:
            # If it's a plain string like "tomorrow" or "next Monday", just show it
            print(f"📅 {name} — due: {due_date} ({urgency})")
            continue
        
        time_left = due - now
        
        if time_left < timedelta(0):
            print(f"⚠️  OVERDUE: {name}")
        elif time_left < timedelta(hours=2):
            print(f"🔴 Due very soon: {name} ({due_date})")
        elif time_left < timedelta(hours=24):
            print(f"🟡 Due today: {name} ({due_date})")
        elif time_left < timedelta(days=3):
            print(f"🟢 Coming up: {name} ({due_date})")

@scheduler.scheduled_job('interval', minutes=1)
def scheduled_check():
    check_tasks()

if __name__ == "__main__":
    setup_database()
    print("🔔 Nag scheduler running. Press Ctrl+C to stop.")
    print("Checking tasks every minute...\n")
    check_tasks()  # Run once immediately on start
    scheduler.start()