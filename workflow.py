import json
import re
from .crew import build_crew

def _extract_json(text: str):
    text = str(text).strip()
    # Remove common markdown fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("The model did not return valid JSON.")

def run_email_workflow(email: dict) -> dict:
    crew = build_crew(email)
    result = crew.kickoff()
    outputs = list(result.tasks_output)

    merged = {}
    for output in outputs:
        try:
            data = _extract_json(output.raw)
            if isinstance(data, dict):
                merged.update(data)
        except Exception:
            continue

    return {
        "purpose": merged.get("purpose", ""),
        "summary": merged.get("summary", ""),
        "key_points": merged.get("key_points", merged.get("key_facts", [])),
        "action_items": merged.get("action_items", []),
        "priority": merged.get("priority", "NORMAL"),
        "priority_reason": merged.get("priority_reason", ""),
        "deadline": merged.get("deadline"),
        "deadline_source": merged.get("deadline_source"),
    }
