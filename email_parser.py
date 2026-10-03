def normalize_email(subject: str, sender: str, body: str) -> dict:
    return {
        "subject": (subject or "").strip(),
        "sender": (sender or "").strip(),
        "body": (body or "").strip(),
    }
