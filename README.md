# ✉️ MailMind AI — Email Summarizer Agent

A hackathon-ready multi-agent email intelligence app built with **CrewAI + Streamlit + Groq GPT-OSS 120B**.

## Workflow

Email → Analyzer Agent → Summarizer Agent → Action Agent → Priority Agent → Reminder automation → Streamlit dashboard

## Features

- Paste an email and analyze it with a coordinated CrewAI team.
- Concise executive summary.
- Key points.
- Action items with owner/deadline when explicitly available.
- Priority classification: URGENT / IMPORTANT / NORMAL.
- Deadline extraction with a no-invention rule.
- Generates an `.ics` calendar reminder when a reliable deadline is found.
- API key stays in Streamlit Secrets.
- Clean responsive Streamlit interface.

## Current stack

- Python 3.13
- CrewAI 1.15.22
- Streamlit 1.64.0
- Groq API
- `openai/gpt-oss-120b`
- LiteLLM provider integration

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload this project exactly as structured.
3. Connect the repository to Streamlit Community Cloud.
4. Set the main file to `app.py`.
5. In Streamlit Cloud, open **App settings → Secrets**.
6. Add:

```toml
GROQ_API_KEY = "your_key"
GROQ_MODEL = "openai/gpt-oss-120b"
```

7. Deploy.

## Important

Do not commit `.streamlit/secrets.toml`. Only commit `.streamlit/secrets.toml.example`.

## Architecture

```text
                    ┌─────────────────────┐
                    │    Streamlit UI     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   CrewAI Workflow   │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   Analyzer Agent       Summarizer Agent      Action Agent
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                       Priority Agent
                               │
                               ▼
                    Reminder Automation
                         (.ics file)
```

## Notes

The reminder automation is intentionally lightweight and deployment-safe: Streamlit generates a calendar event file rather than pretending to run a persistent background scheduler on a serverless-style app.
