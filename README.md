# Nag 🔔

A personal AI agent that remembers what you need to do — and actually reminds you.

## The problem

Most task apps require you to open them, maintain them, and remember to check them. Nag works the other way: you send it a message on WhatsApp, and it reaches out to you at the right time with the right reminder.

## How it works

1. **Send Nag a task** via WhatsApp — as casually as you want
   - *"dentist appointment next friday"*
   - *"remember to call mum"*
   - *"pay rent on the 1st"*

2. **Nag understands it** — powered by Claude AI, it extracts the task, urgency, and due date. If it needs more info, it asks.

3. **Nag reminds you** — it sends WhatsApp nudges at the right time, more frequently as deadlines approach. Every morning it sends a digest of what's due today.

## Features

- 📲 **WhatsApp input and output** — no app to open, no dashboard to check
- 🧠 **AI-powered parsing** — understands messy natural language
- 📅 **Smart date parsing** — "next Monday", "in 3 days", "June 10" all work
- ⏰ **Deadline-aware nudges** — nudge frequency increases as due date approaches
- ☀️ **Morning digest** — daily 9am summary of what's due today
- ✅ **Manage via WhatsApp** — reply "list", "done 1", or "done all"

## Commands

| Command | Description |
|---|---|
| Any text | Add a new task |
| `list` | See all pending tasks |
| `done <number>` | Mark a task as done |
| `done all` | Clear all tasks |

## Tech stack

- **Python** — core language
- **Claude API (Anthropic)** — natural language understanding and task parsing
- **FastAPI** — webhook server to receive WhatsApp messages
- **SQLite** — lightweight local database
- **Twilio** — WhatsApp messaging (send and receive)
- **APScheduler** — task scheduling and nudge timing
- **Railway** — cloud deployment (runs 24/7)

## Architecture

```
WhatsApp → Twilio → FastAPI webhook → Claude API → SQLite
                                                      ↓
WhatsApp ← Twilio ←————————— APScheduler (nudges) ←——
```

## Running locally

1. Clone the repo
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your credentials:
   ```
   ANTHROPIC_API_KEY=your_key
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   TWILIO_WHATSAPP_TO=whatsapp:+yournumber
   ```
4. Start the webhook server:
   ```bash
   uvicorn webhook:app --reload
   ```
5. Start the scheduler in a separate terminal:
   ```bash
   python scheduler.py
   ```

## Project status

Fully functional and deployed. Potential next steps:
- Multi-user support
- Recurring tasks
- Natural language to mark tasks done ("I did the dentist")
- Web dashboard to view and manage tasks
