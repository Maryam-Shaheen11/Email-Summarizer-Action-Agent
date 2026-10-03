import html
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
#MainMenu, footer {visibility: hidden;}
.block-container {max-width: 1180px; padding-top: 1.8rem; padding-bottom: 3rem;}

.hero {
    padding: 1.7rem 2rem; border-radius: 22px; margin-bottom: 1.4rem; color: #fff;
    background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 55%, #db2777 100%);
    box-shadow: 0 12px 32px rgba(79,70,229,.30);
}
.hero h1 {margin: 0 0 .35rem 0; font-size: 2.3rem; color: #fff; letter-spacing: -.5px;}
.hero p {margin: 0 0 .9rem 0; opacity: .92; font-size: 1.04rem; max-width: 720px;}
.chip {display: inline-block; padding: .28rem .75rem; margin: 0 .4rem .3rem 0; border-radius: 999px;
       background: rgba(255,255,255,.18); font-size: .8rem; font-weight: 600;}

.card {
    border: 1px solid rgba(127,127,127,.22); border-radius: 16px; padding: 1rem 1.2rem;
    margin: .5rem 0; background: rgba(127,127,127,.05);
    transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
.card:hover {transform: translateY(-2px); border-color: #7c3aed; box-shadow: 0 8px 20px rgba(124,58,237,.18);}
.card b {font-size: 1rem;}
.small {opacity: .7; font-size: .88rem;}

.stat {
    border-radius: 16px; padding: 1rem 1.2rem; text-align: center; min-height: 104px;
    border: 1px solid rgba(127,127,127,.22); background: rgba(127,127,127,.05);
}
.stat .label {opacity: .65; font-size: .78rem; text-transform: uppercase; letter-spacing: .8px; margin-bottom: .45rem;}
.stat .value {font-size: 1.45rem; font-weight: 700; line-height: 1.2;}
.stat .sub {opacity: .7; font-size: .85rem; margin-top: .25rem;}

.badge {display: inline-block; padding: .3rem 1rem; border-radius: 999px; font-weight: 700;
        font-size: 1rem; color: #fff; letter-spacing: .5px;}
.b-URGENT {background: #ef4444;}
.b-IMPORTANT {background: #f59e0b;}
.b-NORMAL {background: #22c55e;}

.kp {border-left: 4px solid #7c3aed; padding: .6rem 1rem; margin: .5rem 0;
     border-radius: 8px; background: rgba(124,58,237,.08);}
.pill {display: inline-block; padding: .35rem .8rem; border-radius: 999px; margin: .15rem .4rem .15rem 0;
       border: 1px solid rgba(127,127,127,.28); font-size: .85rem;}
.stButton > button, .stDownloadButton > button {border-radius: 10px; font-weight: 600;}
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
    "🏆 Hackathon": {
        "subject": "Hackathon final submission reminder",
        "sender": "hackathon@pakangels.example.com",
        "body": "Hello participants,\n\nThe final submission window closes on October 5, 2026 at 11:59 PM. Each team must submit the GitHub repository link, a live demo link and a 2-minute demo video. Teams that miss the deadline will not be judged. Please make sure your app is deployed and working before submitting.\n\nGood luck,\nHackathon Team",
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


def due_label(dt):
    days = (dt.date() - datetime.now().date()).days
    if days > 1:
        return f"Due in {days} days"
    if days == 1:
        return "Due tomorrow"
    if days == 0:
        return "Due today"
    return f"Overdue by {abs(days)} day{'s' if abs(days) > 1 else ''}"


if "result" not in st.session_state:
    st.session_state.result = None

# ---------------- Sidebar ----------------
with st.sidebar:
    st.markdown("## ✉️ MailMind AI")
    st.caption("Multi-agent email intelligence")
    st.divider()
    st.markdown("**How it works**")
    st.markdown("1. 🔎 Analyze\n2. 📝 Summarize\n3. ✅ Extract actions\n4. 🚦 Prioritize\n5. 📅 Schedule reminder")
    st.divider()
    st.markdown("**⚡ Try a sample email**")
    for name in SAMPLES:
        st.button(name, on_click=load_sample, args=(name,), use_container_width=True, key=f"s_{name}")
    st.button("🧹 Clear all", on_click=clear_all, use_container_width=True)
    st.divider()
    st.caption("Powered by CrewAI + Groq GPT-OSS 120B")

# ---------------- Hero ----------------
st.markdown("""
<div class="hero">
<h1>✉️ MailMind AI</h1>
<p>Turn long emails into clear decisions, action items and real Google Calendar reminders, powered by a team of AI agents.</p>
<span class="chip">🤖 4 AI agents</span><span class="chip">⚡ Results in seconds</span><span class="chip">📅 Google Calendar sync</span>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.25, .75], gap="large")

with left:
    st.markdown("### Email input")
    subject = st.text_input("Subject", placeholder="e.g. Project submission deadline", key="subject")
    sender = st.text_input("Sender", placeholder="e.g. project.manager@example.com", key="sender")
    email_text = st.text_area("Email content", height=270, placeholder="Paste the full email here...", key="body")
    words = len(email_text.split())
    st.caption(f"{words} words" if words else "Tip: use a sample from the sidebar to try it instantly.")
    run = st.button("✨ Analyze email", type="primary", use_container_width=True)

with right:
    st.markdown("### What you get")
    st.markdown("""
    <div class="card"><b>📝 Smart summary</b><br><span class="small">What the email is about, in seconds.</span></div>
    <div class="card"><b>✅ Action checklist</b><br><span class="small">Tick tasks off and track your progress.</span></div>
    <div class="card"><b>🚦 Priority detection</b><br><span class="small">Urgent, important or normal, with the reason.</span></div>
    <div class="card"><b>📅 Calendar reminders</b><br><span class="small">One click adds the deadline to Google Calendar.</span></div>
    """, unsafe_allow_html=True)

# ---------------- Run analysis ----------------
if run:
    if not email_text.strip():
        st.error("Please paste an email before analyzing.")
    elif not st.secrets.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets before running the app.")
    else:
        normalized = normalize_email(subject, sender, email_text)
        for k in [k for k in st.session_state if str(k).startswith("act_")]:
            del st.session_state[k]
        with st.status("Agent team is working...", expanded=True) as status:
            try:
                st.write("🔎 Analyzer Agent is reading the email")
                st.write("📝 Summarizer, ✅ Action and 🚦 Priority agents are collaborating")
                result = run_email_workflow(normalized)
                status.update(label="Analysis complete", state="complete", expanded=False)
                st.session_state.result = result
                st.toast("Analysis complete", icon="✅")
            except Exception as exc:
                status.update(label="Analysis failed", state="error", expanded=True)
                st.exception(exc)

# ---------------- Results ----------------
result = st.session_state.result
if result:
    st.divider()
    st.markdown("## Analysis")

    priority = str(result.get("priority", "NORMAL")).upper()
    if priority not in ("URGENT", "IMPORTANT", "NORMAL"):
        priority = "NORMAL"
    actions = result.get("action_items", [])
    deadline = result.get("deadline")

    guess = None
    if deadline:
        try:
            guess = guess_datetime(deadline, result.get("deadline_source"))
        except Exception:
            guess = None

    if guess:
        dl_value = guess.strftime("%d %b %Y")
        dl_sub = f"{guess.strftime('%I:%M %p')} · {due_label(guess)}"
    else:
        dl_value = str(deadline) if deadline else "No deadline"
        dl_sub = "Nothing to schedule" if not deadline else ""

    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div class="stat"><div class="label">Priority</div><span class="badge b-{priority}">{priority}</span></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat"><div class="label">Action items</div><div class="value">{len(actions)}</div><div class="sub">to complete</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat"><div class="label">Deadline</div><div class="value">{html.escape(dl_value)}</div><div class="sub">{html.escape(dl_sub)}</div></div>', unsafe_allow_html=True)
    st.write("")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "✅ Action items", "📅 Reminder", "🤖 Agent details"])

    with tab1:
        st.markdown("### Executive summary")
        st.write(result.get("summary", "No summary returned."))
        st.markdown("### Key points")
        for point in result.get("key_points", []):
            st.markdown(f'<div class="kp">{html.escape(str(point))}</div>', unsafe_allow_html=True)
        if result.get("priority_reason"):
            st.info(f"**Why this priority:** {result['priority_reason']}")
        with st.expander("📋 Copy summary"):
            st.code(result.get("summary", ""), language=None)

    with tab2:
        if not actions:
            st.success("No explicit action items were detected.")
        else:
            done = sum(1 for i in range(len(actions)) if st.session_state.get(f"act_{i}", False))
            st.progress(done / len(actions), text=f"{done} of {len(actions)} completed")
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
                st.success("All tasks completed. Great work! 🎉")

    with tab3:
        if deadline:
            st.markdown("### Schedule a reminder")
            st.caption("Adjust the date and time if needed, then add it to your calendar.")
            base = guess or datetime.now().replace(minute=0, second=0, microsecond=0)

            c1, c2 = st.columns(2)
            pick_date = c1.date_input("📅 Date", value=base.date(), key=f"d_{deadline}")
            pick_time = c2.time_input("⏰ Time", value=base.time(), key=f"t_{deadline}")
            start_dt = datetime.combine(pick_date, pick_time)
            st.caption(f"📌 {start_dt.strftime('%A, %d %B %Y at %I:%M %p')} · {due_label(start_dt)}")

            if st.button("🔔 Add to Google Calendar", type="primary", use_container_width=True):
                try:
                    actions_text = "\n".join(
                        a.get("task", "") if isinstance(a, dict) else str(a) for a in actions
                    )
                    with st.spinner("Adding to your calendar..."):
                        link = add_reminder(
                            title=f"📧 {result.get('summary', 'Email reminder')[:80]}",
                            start_dt=start_dt,
                            description=actions_text,
                        )
                    st.toast("Reminder added to Google Calendar", icon="✅")
                    st.success(f"Reminder added for {start_dt.strftime('%d %b %Y, %I:%M %p')}")
                    if link:
                        st.link_button("Open in Google Calendar", link)
                except Exception as e:
                    st.error(f"Could not add the reminder: {e}")

            ics = build_ics(
                summary=result.get("summary", "Email reminder"),
                deadline=deadline,
                action=actions,
            )
            st.download_button("📥 Download .ics file", data=ics, file_name="mailmind_reminder.ics",
                               mime="text/calendar", use_container_width=True)
            st.caption("Your email is never stored by this app.")
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
