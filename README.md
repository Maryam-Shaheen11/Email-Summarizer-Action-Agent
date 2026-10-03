
# 📧 Email Summarizer (Multi-Agent Email Action Agent)

Turn long emails into a clear summary, action items, priority and a calendar reminder, using a team of AI agents.

🔗 **Live App:** https://email-summarizer-action-agent.streamlit.app/

---

## Problem

People get many long emails every day. Important tasks and deadlines are hidden inside the text and are easy to miss.

## Solution

Paste an email and four AI agents analyze it. The app shows what the email is about, what you need to do, how urgent it is, and sends a calendar reminder before the deadline.

## Features

- 📝 **Smart summary:** what the email is about, in seconds
- ✅ **Action checklist:** tasks with owner and due date, tick them off as you go
- 🚦 **Priority detection:** Urgent, Important or Normal, with the reason
- 📅 **Calendar reminder:** invite sent to your inbox with alerts, or download the `.ics` file
- ⚡ **Sample emails:** try the app quickly without writing your own email

## How It Works

1. Paste an email (subject, sender, text) or pick a sample
2. Four AI agents analyze it one after another
3. See the summary, action items, priority and deadline
4. Pick a date and time for the reminder
5. Get a calendar invite in your inbox

## The 4 AI Agents

| Agent | Job |
|---|---|
| Email Analyzer | Reads the email and understands the topic and key details |
| Summarizer | Writes a short, clear summary |
| Action Extractor | Finds tasks, owners and deadlines |
| Priority Detector | Decides Urgent, Important or Normal, with the reason |

## High-Level Flow

```
User → Streamlit App → CrewAI (4 Agents + Groq LLM) → Results → Calendar Reminder
```

## Tech Stack

| Component | Technology |
|---|---|
| User interface | Streamlit |
| Language | Python |
| Agent framework | CrewAI |
| AI model | Groq, GPT-OSS 120B |
| Reminder | Calendar
