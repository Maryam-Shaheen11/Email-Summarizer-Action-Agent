import streamlit as st
from src.email_parser import normalize_email
from src.workflow import run_email_workflow
from src.calendar_utils import build_ics

st.set_page_config(
    page_title="MailMind AI",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --accent:#6c63ff; }
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
.hero {
    padding: 1.4rem 1.6rem; border:1px solid rgba(127,127,127,.18);
    border-radius:22px; background: linear-gradient(135deg, rgba(108,99,255,.13), rgba(0,0,0,.02));
    margin-bottom:1.2rem;
}
.hero h1 {margin:0 0 .35rem 0; font-size:2.35rem;}
.hero p {margin:0; opacity:.78; font-size:1.02rem;}
.card {
    border:1px solid rgba(127,127,127,.18); border-radius:18px;
    padding:1.15rem 1.2rem; margin:.55rem 0; background:rgba(127,127,127,.035);
}
.small {opacity:.68; font-size:.88rem;}
.pill {display:inline-block; padding:.35rem .7rem; border-radius:999px;
       border:1px solid rgba(127,127,127,.2); margin-right:.35rem; font-size:.85rem;}
</style>
""", unsafe_allow_html=True)

if "result" not in st.session_state:
    st.session_state.result = None

with st.sidebar:
    st.markdown("## ✉️ MailMind AI")
    st.caption("Multi-agent email intelligence")
    st.divider()
    st.markdown("**Pipeline**")
    st.markdown("1. 🔎 Analyze\n2. 📝 Summarize\n3. ✅ Extract actions\n4. 🚦 Prioritize\n5. 📅 Automate reminder")
    st.divider()
    st.caption("Powered by CrewAI + Groq GPT-OSS 120B")

st.markdown("""
<div class="hero">
<h1>✉️ MailMind AI</h1>
<p>Turn long emails into clear decisions, actions and reminders — using a coordinated AI agent team.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1.25, .75], gap="large")

with left:
    st.markdown("### Email input")
    subject = st.text_input("Subject", placeholder="e.g. Project submission deadline")
    sender = st.text_input("Sender", placeholder="e.g. project.manager@example.com")
    email_text = st.text_area(
        "Paste email content",
        height=310,
        placeholder="Paste the full email here..."
    )
    run = st.button("✨ Analyze Email", type="primary", use_container_width=True)

with right:
    st.markdown("### What you get")
    st.markdown("""
    <div class="card"><b>📝 Smart summary</b><br><span class="small">A concise explanation of what the email is about.</span></div>
    <div class="card"><b>✅ Action items</b><br><span class="small">Tasks, owners and deadlines extracted from the email.</span></div>
    <div class="card"><b>🚦 Priority</b><br><span class="small">Urgent, important or normal with a reason.</span></div>
    <div class="card"><b>📅 Automation</b><br><span class="small">A calendar reminder file is generated when a clear deadline is found.</span></div>
    """, unsafe_allow_html=True)

if run:
    if not email_text.strip():
        st.error("Please paste an email before analyzing.")
    elif not st.secrets.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is missing. Add it in Streamlit Secrets before running the app.")
    else:
        normalized = normalize_email(subject, sender, email_text)
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

    priority = result.get("priority", "NORMAL").upper()
    priority_icon = {"URGENT":"🔴", "IMPORTANT":"🟠", "NORMAL":"🟢"}.get(priority, "⚪")

    m1, m2, m3 = st.columns(3)
    m1.metric("Priority", f"{priority_icon} {priority}")
    m2.metric("Actions", str(len(result.get("action_items", []))))
    m3.metric("Deadline", result.get("deadline") or "None found")

    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Action items", "Automation", "Agent details"])

    with tab1:
        st.markdown("### 📝 Executive summary")
        st.write(result.get("summary", "No summary returned."))
        st.markdown("### 🎯 Key points")
        for point in result.get("key_points", []):
            st.markdown(f"- {point}")
        if result.get("priority_reason"):
            st.info(f"**Why this priority:** {result['priority_reason']}")

    with tab2:
        actions = result.get("action_items", [])
        if not actions:
            st.success("No explicit action items were detected.")
        for i, item in enumerate(actions, 1):
            if isinstance(item, dict):
                task = item.get("task", "Action")
                owner = item.get("owner") or "Not specified"
                due = item.get("due_date") or "No deadline"
                st.markdown(f"**{i}. {task}**  \nOwner: {owner} · Due: {due}")
            else:
                st.markdown(f"**{i}.** {item}")

    with tab3:
        deadline = result.get("deadline")
        if deadline:
            st.success(f"📅 Reminder detected for **{deadline}**.")
            ics = build_ics(
                summary=result.get("summary", "Email reminder"),
                deadline=deadline,
                action=result.get("action_items", []),
            )
            st.download_button(
                "📥 Add reminder to Calendar (.ics)",
                data=ics,
                file_name="mailmind_reminder.ics",
                mime="text/calendar",
                use_container_width=True,
            )
            st.caption("The .ics file can be opened/imported in calendar applications. The app does not store your email.")
        else:
            st.info("No reliable deadline was found, so no reminder was created.")
            st.caption("This avoids creating a false reminder from an ambiguous date.")

    with tab4:
        st.markdown("### Agent pipeline")
        for label in ["Analyzer Agent", "Summarizer Agent", "Action Agent", "Priority Agent"]:
            st.markdown(f'<span class="pill">✓ {label}</span>', unsafe_allow_html=True)
        st.markdown("### Raw structured result")
        st.json(result)
