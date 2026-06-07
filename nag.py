from parser import parse_task, parse_due_date, merge_followup
from database import setup_database, add_task, list_tasks, mark_done, set_due_date, update_task_name

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
                for i, t in enumerate(tasks, start=1):
                    id, task, urgency, needs_date, due_date, follow_up, last_nudged = t
                    date_str = f" | due: {due_date}" if due_date else ""
                    followup_str = f"\n   ❓ {follow_up}" if follow_up else ""
                    print(f"  [{i}] ({urgency}) {task}{date_str}{followup_str}")
            print()

        elif user_input.lower() == "done all":
            tasks = list_tasks()
            if not tasks:
                print("No pending tasks.\n")
            else:
                for t in tasks:
                    mark_done(t[0])
                print(f"✅ All {len(tasks)} tasks marked as done.\n")

        elif user_input.lower().startswith("done "):
            try:
                display_num = int(user_input.split()[1])
                tasks = list_tasks()
                if display_num < 1 or display_num > len(tasks):
                    print(f"No task number {display_num}.\n")
                else:
                    real_id = tasks[display_num - 1][0]
                    mark_done(real_id)
                    print(f"✅ Task {display_num} marked as done.\n")
            except:
                print("Usage: done <number> or done all\n")

        
        else:
            print("Thinking...")
            result = parse_task(user_input)

            
            if not result.get("task"):
                    print("Hmm, I didn't catch a task there. Try again.\n")
            else:
                task_id = add_task(result)
                task_name = result["task"]

                # Step 1: if needs a date, ask for it first
                if result["needs_date"]:
                    due_raw = input("📅 When? (e.g. 'tomorrow', 'June 10', 'next Monday'): ").strip()
                    if due_raw:
                        print("Parsing date...")
                        due_parsed = parse_due_date(due_raw)
                        set_due_date(task_id, due_parsed)
                        print(f"✅ Saved: {task_name} — due {due_parsed} ({result['urgency']})")

                # Step 2: if there's a follow-up and it's NOT about the date, ask it
                follow_up = result["follow_up_question"]
                if follow_up and not result["needs_date"]:
                    answer = input(f"❓ {follow_up} ").strip()
                    if answer:
                        updated_name = merge_followup(task_name, follow_up, answer)
                        update_task_name(task_id, updated_name)
                        print(f"✅ Saved: {updated_name} ({result['urgency']})\n")
                    else:
                        print(f"✅ Saved: {task_name} ({result['urgency']})\n")
                elif not result["needs_date"]:
                    print(f"✅ Saved: {task_name} ({result['urgency']})\n")
                else:
                    print()

if __name__ == "__main__":
    main()