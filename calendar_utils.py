from datetime import datetime, timedelta, timezone

def _escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def build_ics(summary: str, deadline: str, action) -> str:
    # All-day calendar event: avoids timezone assumptions.
    try:
        dt = datetime.strptime(deadline, "%Y-%m-%d")
        date_value = dt.strftime("%Y%m%d")
        next_value = (dt + timedelta(days=1)).strftime("%Y%m%d")
    except ValueError:
        raise ValueError("Deadline must be YYYY-MM-DD.")

    action_text = ""
    if isinstance(action, list) and action:
        action_text = " Actions: " + " | ".join(
            (a.get("task", str(a)) if isinstance(a, dict) else str(a)) for a in action
        )

    uid = f"mailmind-{date_value}@email-summarizer-agent"
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MailMind AI//Email Reminder//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now}",
        f"DTSTART;VALUE=DATE:{date_value}",
        f"DTEND;VALUE=DATE:{next_value}",
        f"SUMMARY:{_escape('Email deadline: ' + summary[:80])}",
        f"DESCRIPTION:{_escape(summary + action_text)}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])
