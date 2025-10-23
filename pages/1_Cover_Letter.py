# pages/1_Cover_Letter.py — Main generator (auth required)
import datetime
import os
import uuid
import streamlit as st
from firebase_admin import auth as admin_auth
import firebase_init
from db_ops import (
    ensure_user_profile,
    create_session,
    save_letter,
    upsert_final_and_metric,
    save_feedback,
    log_interaction,
)
from core_llm import generate_cover_letter, build_prompt

def _first(v):
    return v[0] if isinstance(v, list) else v

def _utc_now_iso():
    return datetime.datetime.now(datetime.UTC).isoformat()

def _autosave_final(action: str):
    sid = st.session_state.get("SESSION_ID")
    if not sid:
        return None
    final_text = (
    st.session_state.get("EDIT_DRAFT", "")
    or st.session_state.get("DRAFT_TEXT", "")
).strip()
    if not final_text:
        return None
    edit_distance = upsert_final_and_metric(UID, sid, final_text)
    try:
        log_interaction(
            UID,
            user_email,
            sid,
            "final_saved",
            {
                "final_text": final_text,
                "edit_distance": edit_distance,
                "triggered_by": action,
            },
        )
    except Exception as e:
        print("Logging final_saved failed:", e)
    return {"final_text": final_text, "edit_distance": edit_distance}


st.set_page_config(page_title="Genie-Hi: Write your first Hi", page_icon="💌")

st.sidebar.caption("made with curiosity and love — by Gabrielle Yang")
# # --- Firestore heartbeat (one-time test) ---
# from db_ops import log_interaction
# try:
#     _ = log_interaction(
#         uid="debug-uid",
#         session_id="debug-session",
#         event_type="heartbeat",
#         payload={"source": "startup"}
#     )
#     print("DEBUG: heartbeat write attempted to 'interaction_logs'")
# except Exception as e:
#     print("ERROR: heartbeat write failed:", e)
# # --- end heartbeat ---


def _first(v):
    return v[0] if isinstance(v, list) else v


# If user not in session, try to restore from id_token in the URL
if "user" not in st.session_state:
    token = _first(st.query_params.get("id_token"))
    if token:
        try:
            decoded = admin_auth.verify_id_token(token)
            st.session_state["user"] = {
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
            }
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
sid = st.session_state.get("SESSION_ID")
if not sid:
    # create placeholder session to avoid sid not defined errors
    sid = create_session(UID, resume_text="", jd_text="")
    st.session_state["SESSION_ID"] = sid
# --------------------------
# YOUR UI STARTS ↓
# --------------------------

st.title("Generate your personalized cover letter")

# Inputs
resume = st.text_area(
    "Resume", height=220, placeholder="Paste your resume…", key="resume"
)
jd = st.text_area("Job Description", height=220, placeholder="Paste the JD…", key="jd")

c1, c2, c3 = st.columns(3)
with c1:
    format_choice = st.selectbox(
        "Format",
        ["blurb for referral", "Short message in chat", "Formal cover letter"],
        index=0,
        key="format_choice",
    )
with c2:
    length_pref = st.selectbox(
        "Length",
        ["one-paragraph", "2-3 paragraphs", "3-5 paragraphs"],
        index=1,
        key="length_pref",
    )
highlights = st.text_input("Highlights (comma-separated)")

# State
if "SESSION_ID" not in st.session_state:
    st.session_state["SESSION_ID"] = ""
if "DRAFT_TEXT" not in st.session_state:
    st.session_state["DRAFT_TEXT"] = ""
if "FINAL_TEXT" not in st.session_state:
    st.session_state["FINAL_TEXT"] = ""
if "draft_view" not in st.session_state:
    st.session_state["draft_view"] = ""

# Generate
if st.button("✨ Generate Draft", key="gen_btn"):
    prompt = build_prompt(
        resume=resume,
        jd=jd,
        highlights=highlights,
        length_style=length_pref,
        format_style=format_choice,
    )
    gen_id = uuid.uuid4().hex
    st.session_state["GEN_ID"] = gen_id
    st.session_state["GEN_NUM"] = (st.session_state.get("GEN_NUM", 0) or 0) + 1
    gen_num = st.session_state["GEN_NUM"]
    
    draft = generate_cover_letter(prompt)
    # sid = create_session(
    #     UID,
    #     resume_text=resume,
    #     jd_text=jd,
    #     length_pref=length_pref,
    #     highlights=highlights,
    #     model=os.getenv("VERTEX_MODEL", "gemini-2.5-flash"),
    #     prompt_version="p1.0",
    # )
    save_letter(UID, sid, draft, "draft")
    st.session_state["SESSION_ID"] = sid
    st.session_state["DRAFT_TEXT"] = draft
    st.session_state["_LAST_EDIT_SNAPSHOT"] = draft
    st.session_state["EDIT_DRAFT"] = draft
    st.session_state["EDIT_VERSION"] = 0
    st.session_state["_NO_EDIT_LOGGED"] = False

    try:
        log_interaction(
            UID,
            user_email,
            sid,
            "draft_generated",
            {
                "gen_id": gen_id,
                "gen_num": gen_num,
                "resume": resume,
                "job_description": jd,
                "highlights": highlights,
                "length_pref": length_pref,
                "format_choice": format_choice,
                "model": os.getenv("VERTEX_MODEL", "gemini-2.5-flash"),
                "draft_text": draft,
            },
        )
    except Exception as e:
        print("Logging draft_generated failed:", e)

    st.success("Draft generated. You can edit and save your final below.")

st.markdown("### Draft Preview & Edit")

# -----------------------------------------------------------------------------
# Edit area (user edits directly on model output)
# -----------------------------------------------------------------------------

original_text = st.session_state.get("DRAFT_TEXT", "")

edited_text = st.text_area(
    "Edit directly as you wish",
    value=st.session_state.get("EDIT_DRAFT", original_text),
    height=220,
    key="EDIT_DRAFT",
)


# Versioning logic (edits belong to the *current* generation)
prev_snapshot = st.session_state.get("_LAST_EDIT_SNAPSHOT", original_text)

if edited_text.strip() != prev_snapshot.strip():
    version_num = (st.session_state.get("EDIT_VERSION", 0) or 0) + 1
    st.session_state["EDIT_VERSION"] = version_num
    st.session_state["_LAST_EDIT_SNAPSHOT"] = edited_text

    # 1) persist this edit as its own artifact (the missing piece)
    try:
        save_letter(UID, sid, edited_text, kind=f"edit_v{version_num}")
    except Exception as e:
        print("Saving edit version failed:", e)

    # 2) update latest-final + metrics for the session
    try:
        upsert_final_and_metric(UID, sid, edited_text)
    except Exception as e:
        print("Autosave (upsert_final_and_metric) failed:", e)

    # 3) log edit
    try:
        log_interaction(
            UID,
            user_email,
            sid,
            "edit_version",
            {
                "gen_id": st.session_state.get("GEN_ID"),
                "gen_num": st.session_state.get("GEN_NUM"),
                "version": version_num,
                "timestamp": _utc_now_iso(),
                "edited_text": edited_text,
            },
        )
    except Exception as e:
        print("Logging edit_version failed:", e)
else:
    # Log 'no_edit' only once per generation to avoid spam
    if not st.session_state.get("_NO_EDIT_LOGGED"):
        try:
            ts = datetime.datetime.now(datetime.UTC).isoformat()
            log_interaction(
                UID,
                user_email,
                sid,
                "no_edit",
                {
                    "user_email": user_email,
                    "gen_id": st.session_state.get("GEN_ID"),
                    "gen_num": st.session_state.get("GEN_NUM"),
                    "timestamp": ts,
                    "draft_text": original_text,
                },
            )
            st.session_state["_NO_EDIT_LOGGED"] = True
        except Exception as e:
            print("Logging no_edit failed:", e)

# -----------------------------------------------------------------------------
# Final text to save (latest edit, fallback to original)
# -----------------------------------------------------------------------------


reason = st.text_input(
    "(optional) provide feedback to improve your next experience", key="feedback_reason"
)
st.session_state["feedback"] = reason

c4, c5 = st.columns(2)
with c4:
    if st.button("👍 Looks good", key="thumbs_up"):
        final_info = _autosave_final("thumbs_up")
        sid = st.session_state.get("SESSION_ID")
        if sid:
            save_feedback(UID, user_email, sid, thumb=1, reason=reason.strip())
            try:
                log_interaction(
                    UID,
                    user_email,
                    sid,
                    "feedback_submitted",
                    {
                        "thumb": 1,
                        "feedback": reason.strip(),
                        "final_text": (final_info or {}).get(
                            "final_text", st.session_state.get("FINAL_TEXT", "")
                        ),
                    },
                )
            except Exception as e:
                print("Logging feedback_submitted failed:", e)
            st.success("Thanks! Saved internally.")
        else:
            st.info("Generate a draft first.")
with c5:
    if st.button("👎 Needs work", key="thumbs_down"):
        final_info = _autosave_final("thumbs_down")
        sid = st.session_state.get("SESSION_ID")
        if sid:
            save_feedback(UID, user_email, sid, thumb=-1, reason=reason.strip())
            try:
                log_interaction(
                    UID,
                    user_email,
                    sid,
                    "feedback_submitted",
                    {
                        "thumb": -1,
                        "feedback": reason.strip(),
                        "final_text": (final_info or {}).get(
                            "final_text", st.session_state.get("FINAL_TEXT", "")
                        ),
                    },
                )
            except Exception as e:
                print("Logging feedback_submitted failed:", e)
            st.success("Noted. Saved internally.")
        else:
            st.info("Generate a draft first.")
