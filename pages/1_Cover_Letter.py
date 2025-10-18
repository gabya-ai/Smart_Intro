# pages/1_Cover_Letter.py — Main generator (auth required)
import os
import streamlit as st
from firebase_admin import auth as admin_auth

from db_ops import (
    uid_from_email, ensure_user_profile, create_session,
    save_letter, upsert_final_and_metric, save_feedback
)
from core_llm import generate_cover_letter

st.set_page_config(page_title="Genie-Hi: Write your first Hi", page_icon="💌")

st.sidebar.caption("made with curiosity and love — by Gabrielle Yang")


def _first(v):
    return v[0] if isinstance(v, list) else v

# If user not in session, try to restore from id_token in the URL
if "user" not in st.session_state:
    token = _first(st.query_params.get("id_token"))
    if token:
        try:
            decoded = admin_auth.verify_id_token(token)
            st.session_state["user"] = {"uid": decoded["uid"], "email": decoded.get("email", "")}
        except Exception:
            pass  # fall through to the normal 'not signed in' handling below

# Existing guard (unchanged): if still no user, stop rendering
if "user" not in st.session_state:
    st.warning("You need to sign in first.")
    st.stop()


# --- Auth check: must be signed in ---
firebase_user = st.session_state.get("user")

if not firebase_user:
    st.warning("You need to sign in first.")
    st.stop()

# 3) Gate if still not signed in
if not firebase_user:
    st.warning("You need to sign in first.")
    st.link_button("Back to sign-in", "https://genie-hi-front.web.app")
    st.stop()

UID = firebase_user["uid"]
user_email = firebase_user["email"]
ensure_user_profile(UID, user_email)

# --------------------------
# YOUR UI STARTS ↓
# --------------------------

st.title("Generate your personalized cover letter")

# Inputs
resume = st.text_area("Resume", height=220, placeholder="Paste your resume…", key="resume")
jd     = st.text_area("Job Description", height=220, placeholder="Paste the JD…", key="jd")

c1, c2, c3 = st.columns(3)
with c1: format_choice = st.selectbox("Format", ["blurb for referral","Short message in chat", "Formal cover letter"], index=0, key="format_choice")
with c2: length_pref   = st.selectbox("Length",  ["one-paragraph","2-3 paragraphs","3-5 paragraphs"], index=1, key="length_pref")
highlights = st.text_input("Highlights (comma-separated)")

# State
if "SESSION_ID" not in st.session_state: st.session_state["SESSION_ID"] = ""
if "DRAFT_TEXT" not in st.session_state: st.session_state["DRAFT_TEXT"] = ""
if "FINAL_TEXT" not in st.session_state: st.session_state["FINAL_TEXT"] = ""

def _autosave_final():
    sid = st.session_state.get("SESSION_ID")
    if not sid: return
    text_to_save = (st.session_state.get("FINAL_TEXT","") or st.session_state.get("DRAFT_TEXT","")).strip()
    if text_to_save:
        upsert_final_and_metric(UID, sid, text_to_save)

# Generate
if st.button("✨ Generate Draft", key="gen_btn"):
    draft = generate_cover_letter(
        resume=resume, jd=jd, length_pref=length_pref,
        format_choice=format_choice, highlights=highlights)
    sid = create_session(
        UID, resume_text=resume, jd_text=jd,length_pref=length_pref, highlights=highlights,
        model=os.getenv("VERTEX_MODEL","gemini-2.5-flash"), prompt_version="p1.0"
    )
    save_letter(UID, sid, draft, "draft")
    st.session_state["SESSION_ID"] = sid
    st.session_state["DRAFT_TEXT"] = draft
    st.success(f"Session created: {sid}")

st.markdown("### Draft")
st.text_area("Latest draft", value=st.session_state.get("DRAFT_TEXT",""), height=220, key="draft_view")

reason = st.text_input("(optional) provide your feedback or your final draft to improve your next experience", key="feedback_reason")

c4, c5 = st.columns(2)
with c4:
    if st.button("👍 Looks good", key="thumbs_up"):
        _autosave_final()
        sid = st.session_state.get("SESSION_ID")
        if sid:
            save_feedback(UID, sid, thumb=1, reason=reason.strip())
            st.success("Thanks! Saved internally.")
        else:
            st.info("Generate a draft first.")
with c5:
    if st.button("👎 Needs work", key="thumbs_down"):
        _autosave_final()
        sid = st.session_state.get("SESSION_ID")
        if sid:
            save_feedback(UID, sid, thumb=-1, reason=reason.strip())
            st.success("Noted. Saved internally.")
        else:
            st.info("Generate a draft first.")
