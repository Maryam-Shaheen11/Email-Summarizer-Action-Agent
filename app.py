from datetime import datetime

import streamlit as st
from src.email_parser import normalize_email
from src.workflow import run_email_workflow
from src.calendar_utils import build_ics
from src.google_calendar import add_reminder, guess_datetime

st.set_page_config(
    page_title="MailMind AI",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
.hero {
    padding: 1.6rem 1.8rem; border-radius: 24px; margin-bottom: 1.2rem;
    background: linear-gradient(135deg, #6c63ff 0%, #8e54e9 55%, #ec4899 100%);
    color: #fff; box-shadow: 0 10px 30px rgba(108,99,255,.35);
}
.hero h1 {margin: 0 0 .3rem 0; font-size: 2.4rem; color: #fff;}
.hero p {margin: 0; opacity: .92; font-size: 1.05rem;}
.card {
    border: 1px solid rgba(127,127,127,.2); border-radius: 18px;
    padding: 1rem 1.2rem; margin: .5rem 0; background: rgba(127,127,127,.05);
    transition: transform .15s ease, box-shadow .15s ease;
}
.card:hover {transform: translateY(-3px); box-shadow: 0 8px 22px rgba(108,99,255,.22);}
.small {opacity: .7; font-size: .88rem;}
.stat {
    border-radius: 18px; padding: 1rem 1.2rem; text-align: center;
    border: 1px solid rgba(127,127,127,.2); background: rgba(127,127,127,.05);
}
.stat .label {opacity: .65; font-size: .85rem; margin-bottom: .3rem;}
.stat .value {font-size: 1.5rem; font-weight: 700;}
.badge {display: inline-block; padding: .35rem .95rem; border-radius: 999px;
        font-weight: 700; font-size: 1.05rem; color: #fff;}
.b-URGENT {background: #ef4444;}
.b-IMPORTANT {background: #f59e0b;}
.b-NORMAL {background: #22c55e;}
.pill {display: inline-block; padding: .35rem .7rem; border-radius: 999px;
       border: 1px solid rgba(127,127,127,.25); margin: .15rem .35rem .15rem 0; font-size: .85rem;}
.kp {border-left: 4px solid #6c63ff; padding: .55rem .9rem; margin: .45rem 0;
     border-radius: 8px; background: rgba(108,99,255,.08);}
.stButton > button {border-radius: 12px; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

SAMPLES = {
    "📘 Project deadline": {
        "subject": "Final project submission and meeting",
        "sender": "project.coordinator@example.com",
        "body": "Hi team,\n\nPlease submit your final project report by October 8, 2026 at 5 PM. We will have a short review meeting on October 9 at 10 AM. Everyone should upload their latest report before the deadline and prepare a two-minute explanation of their contribution.\n\nThanks,\nProject Coordinator",
    },
    "🎓 Urgent scholarship": {
        "subject": "URGENT: Scholarship documents required",
        "sender": "admissions@university.edu",
        "body": "Dear Maryam,\n\nYour scholarship application is almost complete. Please send your latest transcript, CNIC copy and recommendation letter by October 6, 2026 at 12 PM. Applications with missing documents will be rejected. Reply to this email once you have uploaded everything.\n\nRegards,\nAdmissions Office",
    },
    "📰 Newsletter": {
        "subject": "Newsletter: October updates",
        "sender": "news@example.com",
        "body": "Hello everyone,\n\nThanks for being part of our community. This month we added new tutorials and a few community stories. Have a look whenever you have time. Nothing is required from you.\n\nBest,\nThe Community Team",
    },
}


def load_sample(name):
    s = SAMPLES[name]
    st.session_state.subject = s["subject"]
    st.session_state.sender = s["sender"]
    st.session_state.body = s["body"]
    st.session_state.result = None


def clear_all():
    st.session_state.subject = ""
    st.session_state.sender = ""
    st.session_state.body = ""
    st.session_state.result = None


if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.markdown("## ✉️ MailMind AI")
    st.caption("Multi-agent email intelligence")
    st.divider()
    st.markdown("**Pipeline**")
    st.markdown("1. 🔎 Analyze\n2. 📝 Summarize\n3. ✅ Extract actions\n4. 🚦 Prioritize\n5. 📅 Automate reminder")
    st.divider()
    st.markdown("**⚡ Try a sample**")
    for name in SAMPLES:
        st.button(name, on_click=load_sample, args=(name,), use_container_width=True, key=f"s_{name}")
    st.button("🧹 Clear", on_click=clear_all, use_container_width=True)
    st.divider()
    st.caption("Powered by CrewAI + Groq GPT-OSS 120B")

st.markdown("""
<div class="hero">
<h1>✉️ MailMind AI</h1>
<p>Turn long emails into clear decisions, actions and real Google Calendar reminders — with a team of AI agents.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.25, .75], gap="large")

with left:
    st.markdown("### Email input")
    subject = st.text_input("Subject", placeholder="e.g. Project submission deadline", key="subject")
    sender = st.text_input("Sender", placeholder="e.g. project.manager@example.com", key="sender")
    email_text = st.text_area("Paste email content", height=280, placeholder="Paste the full email here...", key="body")
    run = st.button("✨ Analyze Email", type="primary", use_container_width=True)

with right:
    st.markdown("### What you get")
    st.markdown("""
    <div class="card"><b>📝 Smart summary</b><br><span class="small">What the email is about, in seconds.</span></div>
    <div class="card"><b>✅ Action checklist</b><br><span class="small">Tick tasks off and track progress.</span></div>
    <div class="card"><b>🚦 Priority</b><br><span class="small">Urgent, important or normal, with a reason.</span></div>
    <div class="card"><b>📅 Real reminders</b><br><span class="small">One click adds the event to your Google Calendar.</span></div>
    """, unsafe_allow_html=True)

if run:
    if not email_text.strip():
        st.error("Please paste an email before analyzing.")
    elif not st.secrets.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets before running the app.")
    else:
        normalized = normalize_email(subject, sender, email_text)
        for k in [k for k in st.session_state if str(k).startswith("act_")]:
            del st.session_state[k]
        with st.status("Running the agent team...", expanded=True) as status:
            try:
                st.write("🔎 Analyzer Agent is understanding the email...")
                result = run_email_workflow(normalized)
                status.update(label="Analysis complete", state="complete", expanded=False)
                st.session_state.result = result
            except Exception as exc:
                status.update(label="Analysis failed", state="error", expanded=True)
                st.exception(exc)

result = st.session_state.result
if result:
    st.divider()
    st.markdown("## Analysis")

    priority = str(result.get("priority", "NORMAL")).upper()
    if priority not in ("URGENT", "IMPORTANT", "NORMAL"):
        priority = "NORMAL"
    actions = result.get("action_items", [])
    deadline = result.get("deadline")

    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div class="stat"><div class="label">Priority</div><span class="badge b-{priority}">{priority}</span></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat"><div class="label">Action items</div><div class="value">{len(actions)}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat"><div class="label">Deadline</div><div class="value">{deadline or "None found"}</div></div>', unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "✅ Action items", "📅 Automation", "🤖 Agent details"])

    with tab1:
        st.markdown("### Executive summary")
        st.write(result.get("summary", "No summary returned."))
        st.markdown("### Key points")
        for point in result.get("key_points", []):
            st.markdown(f'<div class="kp">{point}</div>', unsafe_allow_html=True)
        if result.get("priority_reason"):
            st.info(f"**Why this priority:** {result['priority_reason']}")
        st.markdown("**📋 Copy summary**")
        st.code(result.get("summary", ""), language=None)

    with tab2:
        if not actions:
            st.success("No explicit action items were detected.")
        else:
            done = sum(1 for i in range(len(actions)) if st.session_state.get(f"act_{i}", False))
            st.progress(done / len(actions), text=f"{done} of {len(actions)} done")
            for i, item in enumerate(actions):
                if isinstance(item, dict):
                    task = item.get("task", "Action")
                    owner = item.get("owner") or "Not specified"
                    due = item.get("due_date") or "No deadline"
                    label = f"{task}  ·  👤 {owner}  ·  ⏰ {due}"
                else:
                    label = str(item)
                st.checkbox(label, key=f"act_{i}")
            if done == len(actions):
                st.balloons()

    with tab3:
        if deadline:
            st.success(f"📅 Reminder detected for **{deadline}**.")
            try:
                guess = guess_datetime(deadline, result.get("deadline_source"))
            except Exception:
                guess = datetime.now().replace(minute=0, second=0, microsecond=0)
                st.warning("Date samajh nahi aayi, neeche khud date/time chuno.")

            c1, c2 = st.columns(2)
            pick_date = c1.date_input("📅 Date", value=guess.date(), key=f"d_{deadline}")
            pick_time = c2.time_input("⏰ Time", value=guess.time(), key=f"t_{deadline}")
            start_dt = datetime.combine(pick_date, pick_time)

            if st.button("🔔 Add to my Google Calendar (real reminder)", type="primary", use_container_width=True):
                try:
                    actions_text = "\n".join(
                        a.get("task", "") if isinstance(a, dict) else str(a) for a in actions
                    )
                    link = add_reminder(
                        title=f"📧 {result.get('summary', 'Email reminder')[:80]}",
                        start_dt=start_dt,
                        description=actions_text,
                    )
                    st.success(f"Reminder add ho gaya: {start_dt.strftime('%d %b %Y, %I:%M %p')} ✅")
                    st.balloons()
                    if link:
                        st.link_button("Open in Google Calendar", link)
                except Exception as e:
                    st.error(f"Reminder fail hua: {e}")

            ics = build_ics(
                summary=result.get("summary", "Email reminder"),
                deadline=deadline,
                action=actions,
            )
            st.download_button("📥 Download .ics (backup)", data=ics, file_name="mailmind_reminder.ics",
                               mime="text/calendar", use_container_width=True)
            st.caption("The app does not store your email.")
        else:
            st.info("No reliable deadline was found, so no reminder was created.")
            st.caption("This avoids creating a false reminder from an ambiguous date.")

    with tab4:
        st.markdown("### Agent pipeline")
        for label in ["Analyzer Agent", "Summarizer Agent", "Action Agent", "Priority Agent"]:
            st.markdown(f'<span class="pill">✓ {label}</span>', unsafe_allow_html=True)

        report = (
            f"MailMind AI Report\n\nPriority: {priority}\nDeadline: {deadline or 'None'}\n\n"
            f"Summary:\n{result.get('summary', '')}\n\nKey points:\n"
            + "\n".join(f"- {p}" for p in result.get("key_points", []))
            + "\n\nActions:\n"
            + "\n".join(f"- {a.get('task', '') if isinstance(a, dict) else a}" for a in actions)
        )
        st.download_button("📄 Download report (.txt)", data=report, file_name="mailmind_report.txt",
                           use_container_width=True)
        with st.expander("Raw structured result"):
            st.json(result)
