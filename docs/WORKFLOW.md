# Development Workflow

## 1. Input
The user pastes a subject, sender and email body into Streamlit.

## 2. Analyzer Agent
Identifies purpose, important facts, dates and urgency signals.

## 3. Summarizer Agent
Produces a concise summary and key points. It receives the analyzer output.

## 4. Action Agent
Extracts concrete tasks, owners and deadlines. It does not invent missing information.

## 5. Priority Agent
Uses the email plus previous agent findings to classify priority and identify a reliable deadline.

## 6. Automation
If the deadline is confidently normalized to YYYY-MM-DD, the app creates an `.ics` calendar event for that date. If no reliable deadline exists, it does not create a reminder.

## 7. Presentation
Streamlit displays the results in tabs:
- Summary
- Action items
- Automation
- Agent details

This keeps the UI clean while still showing the multi-agent architecture to hackathon judges.
