import sqlite3
from datetime import datetime

DB_PATH = "nag.db"

def get_connection():
    # Connect to the database (creates the file if it doesn't exist)
    return sqlite3.connect(DB_PATH)

def setup_database():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            urgency TEXT,
            needs_date BOOLEAN,
            follow_up_question TEXT,
            due_date TEXT,
            done BOOLEAN DEFAULT 0,
            created_at TEXT,
            last_nudged TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def add_task(parsed):
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO tasks (task, urgency, needs_date, follow_up_question, done, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (
        parsed["task"],
        parsed["urgency"],
        parsed["needs_date"],
        parsed["follow_up_question"],
        datetime.now().isoformat()
    ))
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def list_tasks():
    conn = get_connection()
    cursor = conn.execute("""
        SELECT id, task, urgency, needs_date, due_date, follow_up_question, last_nudged
        FROM tasks
        WHERE done = 0
        ORDER BY created_at DESC
    """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def mark_done(task_id):
    # Mark a task as completed
    conn = get_connection()
    conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def set_due_date(task_id, due_date):
    conn = get_connection()
    conn.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
    conn.commit()
    conn.close()

def update_last_nudged(task_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET last_nudged = ? WHERE id = ?", 
                (datetime.now().isoformat(), task_id))
    conn.commit()
    conn.close()

def update_task_name(task_id, new_name):
    conn = get_connection()
    conn.execute("UPDATE tasks SET task = ? WHERE id = ?", (new_name, task_id))
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    setup_database()