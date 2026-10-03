import json
from datetime import datetime, timedelta

import streamlit as st
from dateutil import parser as dtparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TZ = "Asia/Karachi"


def _service():
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def parse_deadline(text: str) -> datetime:
    dt = dtparser.parse(str(text))
    has_time = any(c in str(text) for c in (":", "AM", "PM", "am", "pm"))
    if not has_time:
        dt = dt.replace(hour=9, minute=0)  # date only -> 9 AM default
    return dt.replace(tzinfo=None)


def add_reminder(title, deadline_text, description="", duration_min=30):
    start_dt = parse_deadline(deadline_text)
    end_dt = start_dt + timedelta(minutes=duration_min)
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TZ},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TZ},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    created = _service().events().insert(
        calendarId=st.secrets["GOOGLE_CALENDAR_ID"], body=event
    ).execute()
    return created.get("htmlLink")
