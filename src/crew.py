import json
from crewai import Agent, Crew, Process, Task
from .llm import get_llm

def _agent(role, goal, backstory, llm):
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

def build_crew(email: dict):
    llm = get_llm()
    email_json = json.dumps(email, ensure_ascii=False)

    analyzer = _agent(
        "Email Intelligence Analyst",
        "Identify the email's purpose, important facts, dates, urgency signals and context.",
        "You carefully inspect business and personal emails and separate facts from assumptions.",
        llm,
    )
    summarizer = _agent(
        "Executive Email Summarizer",
        "Create a concise, faithful summary that preserves the important meaning.",
        "You turn long emails into short, useful summaries without inventing information.",
        llm,
    )
    action_agent = _agent(
        "Action Item Specialist",
        "Extract concrete tasks, owners and deadlines from the email.",
        "You specialize in converting unstructured email language into actionable work items.",
        llm,
    )
    priority_agent = _agent(
        "Priority and Deadline Analyst",
        "Classify priority and identify the most reliable deadline for automation.",
        "You assess urgency from explicit deadlines, requested response timing and business impact. You never invent a deadline.",
        llm,
    )

    analyze_task = Task(
        description=f"""
Analyze this email:
{email_json}

Return ONLY valid JSON:
{{
  "purpose": "string",
  "key_facts": ["string"],
  "dates_mentioned": ["string"],
  "urgency_signals": ["string"]
}}
""",
        expected_output="Valid JSON with purpose, key_facts, dates_mentioned and urgency_signals.",
        agent=analyzer,
    )

    summarize_task = Task(
        description=f"""
Using the email and the analyst's findings, create a concise summary.

EMAIL:
{email_json}

Return ONLY valid JSON:
{{
  "summary": "2-4 sentence summary",
  "key_points": ["3-6 short points"]
}}
""",
        expected_output="Valid JSON containing summary and key_points.",
        agent=summarizer,
        context=[analyze_task],
    )

    action_task = Task(
        description=f"""
Extract explicit action items from this email:
{email_json}

Return ONLY valid JSON:
{{
  "action_items": [
    {{"task":"string","owner":"string or null","due_date":"string or null"}}
  ]
}}

Do not invent tasks or dates.
""",
        expected_output="Valid JSON containing action_items.",
        agent=action_agent,
        context=[analyze_task],
    )

    priority_task = Task(
        description=f"""
Determine email priority and deadline using the email plus previous findings.

Return ONLY valid JSON:
{{
  "priority": "URGENT | IMPORTANT | NORMAL",
  "priority_reason": "short reason",
  "deadline": "YYYY-MM-DD or null",
  "deadline_source": "exact phrase from email or null"
}}

Rules:
- URGENT: immediate/near-term action, explicit urgent language, or very close deadline.
- IMPORTANT: meaningful action/deadline but not immediate.
- NORMAL: informational or routine.
- If a date cannot be converted confidently to YYYY-MM-DD, return null.
- Never invent a deadline.
Today is provided by the application environment; if relative dates are ambiguous, prefer null.
""",
        expected_output="Valid JSON with priority, priority_reason, deadline and deadline_source.",
        agent=priority_agent,
        context=[analyze_task, action_task],
    )

    crew = Crew(
        agents=[analyzer, summarizer, action_agent, priority_agent],
        tasks=[analyze_task, summarize_task, action_task, priority_task],
        process=Process.sequential,
        verbose=False,
    )
    return crew
