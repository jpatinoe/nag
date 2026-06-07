import sqlite3
from datetime import datetime

DB_PATH = "nag.db"

def get_connection():
    # Connect to the database (creates the file if it doesn't exist)
    return sqlite3.connect(DB_PATH)

def setup_database():
    # Create the tasks table if it doesn't already exist
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
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def add_task(parsed):
    # Insert a new task using the parsed output from Claude
    conn = get_connection()
    conn.execute("""
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
    conn.close()

def list_tasks():
    # Return all tasks that aren't done yet
    conn = get_connection()
    cursor = conn.execute("""
        SELECT id, task, urgency, needs_date, due_date, follow_up_question
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

if __name__ == "__main__":
    setup_database()