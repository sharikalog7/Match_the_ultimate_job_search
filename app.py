# app.py
import streamlit as st
import pandas as pd
from db import JobDB
import ast
import os
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib

load_dotenv()

st.set_page_config(page_title="Sponsorship Job Finder — MVP", layout="wide")
st.title("Sponsorship-aware Job Scraper — MVP")

db = JobDB("jobs.db")
jobs = db.list_jobs()
df = pd.DataFrame(jobs)

if df.empty:
    st.info("No jobs in database. Run `scraper.py` to populate jobs first.")
    st.stop()

# parse stringified dicts back into objects for display convenience
def safe_eval(s):
    try:
        return ast.literal_eval(s)
    except:
        return s

df['h1b_history_parsed'] = df['h1b_history'].apply(lambda x: safe_eval(x) if x else None)
df['diagnostic_parsed'] = df['diagnostic'].apply(lambda x: safe_eval(x) if x else None)

# Filters
col1, col2, col3 = st.columns([2,2,6])
with col1:
    s_flag = st.selectbox("Sponsorship filter", options=["all", "no_sponsorship", "likely_sponsorship", "ambiguous", "unknown"], index=0)
with col2:
    company_filter = st.text_input("Company contains (optional)")
with col3:
    search_term = st.text_input("Title/job contains (optional)")

filtered = df.copy()
if s_flag != "all":
    filtered = filtered[filtered['sponsorship_flag'] == s_flag]
if company_filter:
    filtered = filtered[filtered['company'].str.contains(company_filter, case=False, na=False)]
if search_term:
    filtered = filtered[filtered['title'].str.contains(search_term, case=False, na=False)]

st.write(f"Showing {len(filtered)} jobs.")

# Show table
def make_display_row(r):
    return {
        "id": r['id'],
        "title": r['title'],
        "company": r['company'],
        "location": r['location'],
        "sponsorship_flag": r['sponsorship_flag'],
        "h1b_summary": (r['h1b_history_parsed'] or {}).get('total_cases') if r['h1b_history_parsed'] else None,
        "url": r['url']
    }

display_rows = [make_display_row(r) for _, r in filtered.iterrows()]
display_df = pd.DataFrame(display_rows)

st.dataframe(display_df[['id','title','company','location','sponsorship_flag','h1b_summary','url']], use_container_width=True)

st.markdown("---")
st.header("Job details / Actions")

job_id = st.number_input("Enter job id to inspect", value=int(display_df['id'].iloc[0]), min_value=1, step=1)
job = db.get_job(job_id)
if not job:
    st.warning("Job id not found.")
    st.stop()

st.subheader(f"{job['title']} — {job['company']}")
st.write("**Location:**", job['location'])
st.write("**Sponsorship detection:**", job['sponsorship_flag'])
st.write("**H-1B history (if available):**", job['h1b_history'])
st.write("**Description (snippet):**")
st.code(job['description'][:2000])

st.markdown("### Actions")
# Apply link (redirect to job site)
st.markdown(f"[Open job posting / Apply →]({job['url']})")

# Generate email draft
def generate_email_draft(company, job_url, role_title):
    applicant_name = "Your Name"
    applicant_email = "you@example.com"
    subject = f"Query: Sponsorship policy for {role_title}"
    body = f"""Hello {company} recruiting team,

My name is {applicant_name}. I am interested in the {role_title} role you have posted ({job_url}).

Before applying, could you please confirm whether your company is able to sponsor H-1B visas or accept candidates requiring visa sponsorship/transfer for this position? I would appreciate any details about sponsorship timelines or restrictions.

Thank you for your time — I look forward to hearing from you.

Best regards,
{applicant_name}
{applicant_email}
"""
    return subject, body

subj, body = generate_email_draft(job['company'] or "Recruiter", job['url'], job['title'] or "this role")
st.text_input("Email subject", value=subj, key="email_subj")
st.text_area("Email body", value=body, height=220, key="email_body")

# Optional: send email (configure SMTP via env vars)
SEND_EMAIL = os.getenv("ENABLE_SMTP", "false").lower() in ("1","true","yes")
if SEND_EMAIL:
    st.markdown("**SMTP is enabled**")
    if st.button("Send email now (uses SMTP)"):
        SMTP_HOST = os.getenv("SMTP_HOST")
        SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        SMTP_USER = os.getenv("SMTP_USER")
        SMTP_PASS = os.getenv("SMTP_PASS")
        FROM_ADDR = os.getenv("FROM_ADDR", SMTP_USER)
        TO_ADDR = os.getenv("TO_ADDR", "legal@example.com")  # this should be recruiter or legal contact
        msg = EmailMessage()
        msg["Subject"] = st.session_state.email_subj
        msg["From"] = FROM_ADDR
        msg["To"] = TO_ADDR
        msg.set_content(st.session_state.email_body)
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
                s.starttls()
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
            st.success("Email sent.")
            db.mark_verified(job_id)
        except Exception as e:
            st.error(f"Failed to send: {e}")
else:
    st.info("SMTP email sending is disabled. To enable, set ENABLE_SMTP=true and configure SMTP_* env vars.")

st.markdown("---")
st.caption("This is a proof-of-concept. For production use: use official APIs, ensure legal compliance, and robust scraping / rate-limiting / error handling.")
