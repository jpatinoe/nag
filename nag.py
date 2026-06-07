from parser import parse_task
from database import setup_database, add_task, list_tasks, mark_done, set_due_date

def main():
    setup_database()
    
    print("\n🔔 Nag is running. Type a task, 'list' to see tasks, or 'done <id>' to mark complete.\n")
    
    while True:
        user_input = input("> ").strip()
        
        if not user_input:
            continue
        
        elif user_input.lower() == "list":
            tasks = list_tasks()
            if not tasks:
                print("No pending tasks.")
            else:
                print("\nYour tasks:")
                for t in tasks:
                    id, task, urgency, needs_date, due_date, follow_up = t
                    date_str = f" | due: {due_date}" if due_date else ""
                    followup_str = f"\n   ❓ {follow_up}" if follow_up else ""
                    print(f"  [{id}] ({urgency}) {task}{date_str}{followup_str}")
            print()
        
        elif user_input.lower().startswith("done "):
            try:
                task_id = int(user_input.split()[1])
                mark_done(task_id)
                print(f"✅ Task {task_id} marked as done.\n")
            except:
                print("Usage: done <id>\n")
        
        else:
            print("Thinking...")
            result = parse_task(user_input)
            if not result.get("task"):
                print("Hmm, I didn't catch a task there. Try again.\n")
            else:
                task_id = add_task(result)
                
                if result["follow_up_question"]:
                    print(f"✅ Got it. ❓ {result['follow_up_question']}\n")
                
                if result["needs_date"]:
                    due = input("📅 When? (e.g. 'tomorrow', 'June 10', 'next Monday'): ").strip()
                    if due:
                        set_due_date(task_id, due)
                        print(f"✅ Saved: {result['task']} — due {due} ({result['urgency']})\n")
                    else:
                        print(f"✅ Saved: {result['task']} ({result['urgency']})\n")
                else:
                    print(f"✅ Saved: {result['task']} ({result['urgency']})\n")

if __name__ == "__main__":
    main()