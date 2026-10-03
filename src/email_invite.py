import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import streamlit as st

PK_OFFSET = timedelta(hours=5)  # Asia/Karachi = UTC+5


def _esc(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _fmt(dt):
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_invite_ics(title, start_local, description, attendee, organizer, duration_min=30):
    start = start_local - PK_OFFSET
    end = start + timedelta(minutes=duration_min)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MailMind AI//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@mailmind",
        f"DTSTAMP:{_fmt(datetime.now(timezone.utc))}",
        f"DTSTART:{_fmt(start)}",
        f"DTEND:{_fmt(end)}",
        f"SUMMARY:{_esc(title)}",
        f"DESCRIPTION:{_esc(description)}",
        f"ORGANIZER;CN=MailMind AI:mailto:{organizer}",
        f"ATTENDEE;CN={attendee};RSVP=TRUE;PARTSTAT=NEEDS-ACTION:mailto:{attendee}",
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
    ]
    for trigger in ("-P1D", "-PT1H", "-PT10M"):
        lines += [
            "BEGIN:VALARM",
            f"TRIGGER:{trigger}",
            "ACTION:DISPLAY",
            "DESCRIPTION:Reminder",
            "END:VALARM",
        ]
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"


def send_invite(to_email, title, start_local, description=""):
    sender = st.secrets["GMAIL_ADDRESS"]
    password = st.secrets["GMAIL_APP_PASSWORD"]
    ics = build_invite_ics(title, start_local, description, to_email, sender)

    msg = EmailMessage()
    msg["Subject"] = f"Reminder: {title}"
    msg["From"] = f"MailMind AI <{sender}>"
    msg["To"] = to_email
    msg.set_content(
        f"Your reminder is ready.\n\n{title}\n"
        f"When: {start_local.strftime('%A, %d %B %Y at %I:%M %p')} (PKT)\n\n"
        f"Open the attached invite to add it to your calendar. "
        f"You will be reminded 1 day, 1 hour and 10 minutes before.\n\n"
        f"Sent by MailMind AI"
    )
    msg.add_alternative(ics, subtype="calendar", params={"method": "REQUEST"})
    msg.add_attachment(
        ics.encode("utf-8"), maintype="text", subtype="calendar",
        filename="reminder.ics", params={"method": "REQUEST"},
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(sender, password)
        server.send_message(msg)
