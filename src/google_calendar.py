import json
import re
from datetime import datetime, timedelta

import streamlit as st
from dateutil import parser as dtparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TZ = "Asia/Karachi"

AMPM_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.I)
H24_RE = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)")


def _service():
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def guess_datetime(deadline_text, *extra_texts):
    """Date from deadline, time from deadline text or its source sentence. Default 9 AM."""
    base = dtparser.parse(str(deadline_text))
    hour, minute = 9, 0
    texts = [str(deadline_text)] + [str(t) for t in extra_texts if t]
    for t in texts:
        m = AMPM_RE.search(t)
        if m:
            hour = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
            minute = int(m.group(2) or 0)
            break
        m = H24_RE.search(t)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            break
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=None)


def add_reminder(title, start_dt, description="", duration_min=30):
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
