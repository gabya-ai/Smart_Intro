import os
import uuid
import datetime
# import streamlit.web.server.websocket_headers as st_ws
import streamlit as st

# Must be first Streamlit call
st.set_page_config(page_title="Genie-Hi: Write your first Hi", page_icon="💌")

# Safe to import after page_config
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
from core_llm import generate_cover_letter, build_prompt_cover_letter, build_prompt_suggestion

COOKIE_NAME = "gh_id_token"

# ---------- small utils ----------
def _first(v):
    return v[0] if isinstance(v, list) else v

def _utc_now_iso():
    return datetime.datetime.now(datetime.UTC).isoformat()

def _raw_cookie_header() -> str:
    """Return the raw Cookie header safely across Streamlit versions."""
    try:
        # Preferred in Streamlit ≥1.37
        return getattr(st, "context").headers.get("Cookie", "")
    except Exception:
        # Fallback for older builds
        try:
            import streamlit.web.server.websocket_headers as st_ws
            return st_ws._get_websocket_headers().get("Cookie", "")
        except Exception:
            return ""
        
def _get_cookie():
    cookies = _raw_cookie_header()
    for kv in cookies.split(";"):
        if kv.strip().startswith(f"{COOKIE_NAME}="):
            return kv.split("=", 1)[1].strip()
    return None


# def _clear_cookie():
#     st.markdown(
#         f"""
#         <script>
#         document.cookie = "{COOKIE_NAME}=; path=/; max-age=0;";
#         </script>
#         """,
#         unsafe_allow_html=True,
#     )

def _set_cookie_js(token: str | None):
    """Write or clear cookie via small JS snippet."""
    if token:
        st.markdown(
            f"""
            <script>
            document.cookie = "{COOKIE_NAME}={token}; path=/; max-age={7*24*3600}; SameSite=Lax";
            </script>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <script>
            document.cookie = "{COOKIE_NAME}=; path=/; max-age=0;";
            </script>
            """,
            unsafe_allow_html=True,
        )

def _autosave_final(action: str):
    sid = st.session_state.get("SESSION_ID")
    if not sid:
        return None
    final_text = (st.session_state.get("EDIT_DRAFT", "") or st.session_state.get("DRAFT_TEXT", "")).strip()
    if not final_text:
        return None
    edit_distance = upsert_final_and_metric(UID, sid, final_text)
    try:
        log_interaction(
            UID,
            user_email,
            sid,
            "final_saved",
            {"final_text": final_text, "edit_distance": edit_distance, "triggered_by": action},
        )
    except Exception as e:
        print("Logging final_saved failed:", e)
    return {"final_text": final_text, "edit_distance": edit_distance}

# ---------- unified auth restore (session → URL token → cookie) ----------
def _try_restore_from_session():
    user = st.session_state.get("user")
    if user and user.get("uid"):
        return user
    return None

def _try_restore_from_url_token():
    token = None
    try:
        token = (_first(st.query_params.get("id_token")) if hasattr(st, "query_params") else None)
    except Exception:
        token = None
    if not token:
        return None
    try:
        decoded = admin_auth.verify_id_token(token)
        user_info = {"uid": decoded["uid"], "email": decoded.get("email", "")}
        st.session_state["user"] = user_info
        return user_info
    except Exception:
        return None

def _try_restore_from_cookie():
    raw = _get_cookie()
    if not raw:
        return None
    try:
        decoded = admin_auth.verify_id_token(raw)  # JWT -> claims
        user_info = {"uid": decoded["uid"], "email": decoded.get("email", "")}
        st.session_state["user"] = user_info
        return user_info
    except Exception as e:
        print("Cookie verify error:", e)
        _set_cookie_js(None)
        return None

def restore_user():
    for fn in (_try_restore_from_session, _try_restore_from_url_token, _try_restore_from_cookie):
        user = fn()
        if user:
            return user
    return None

# ---------- page setup ----------
st.sidebar.caption("made with curiosity and love — by Gabrielle Yang")

firebase_user = restore_user()
if not firebase_user:
    st.switch_page("welcome.py")
    st.stop()

UID = firebase_user["uid"]
user_email = firebase_user.get("email", "")
st.write(f"Welcome back, {user_email}" if user_email else "Welcome back!")

ensure_user_profile(UID, user_email)

sid = st.session_state.get("SESSION_ID")
if not sid:
    sid = create_session(UID, resume_text="", jd_text="")
    st.session_state["SESSION_ID"] = sid

# --------------------------
# UI
# --------------------------
st.title("Answer the 'Why me' Question 💌")

resume = st.text_area("Resume", height=220, placeholder="Paste your resume…", key="resume")
jd = st.text_area("Job Description", height=220, placeholder="Paste the JD…", key="jd")

c1, c2, _ = st.columns(3)
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

st.session_state.setdefault("DRAFT_TEXT", "")
st.session_state.setdefault("FINAL_TEXT", "")
st.session_state.setdefault("draft_view", "")

if st.button("✨ Generate Draft", key="gen_btn"):
    gen_id = uuid.uuid4().hex
    st.session_state["GEN_ID"] = gen_id
    st.session_state["GEN_NUM"] = (st.session_state.get("GEN_NUM", 0) or 0) + 1
    gen_num = st.session_state["GEN_NUM"]

    prompt_cover_letter = build_prompt_cover_letter(
        resume=resume, jd=jd, highlights=highlights, length_style=length_pref, format_style=format_choice
    )
    draft = generate_cover_letter(prompt_cover_letter)

    save_letter(UID, sid, draft, "draft")
    st.session_state["DRAFT_TEXT"] = draft
    st.session_state["_LAST_EDIT_SNAPSHOT"] = draft
    st.session_state["EDIT_DRAFT"] = draft
    st.session_state["EDIT_VERSION"] = 0
    st.session_state["_NO_EDIT_LOGGED"] = False

    prompt_suggestions = build_prompt_suggestion(
        resume=resume, jd=jd, highlights=highlights, length_style=length_pref, format_style=format_choice
    )
    suggestions = generate_cover_letter(prompt_suggestions)
    # view-only; no DB write
    st.session_state["SUGGESTIONS_TEXT"] = suggestions
    st.session_state["_LAST_EDIT_SNAPSHOT_SUGGESTIONS"] = suggestions
    st.session_state["EDIT_SUGGESTIONS"] = suggestions
    st.session_state["EDIT_VERSION_SUGGESTIONS"] = 0
    st.session_state["_NO_EDIT_LOGGED_SUGGESTIONS"] = True

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
                "suggestions_text": suggestions,
            },
        )
    except Exception as e:
        print("Logging draft_generated failed:", e)

    st.success("Draft generated. You can edit and save your final below.")

st.markdown("### Draft Preview & Edit")

original_text = st.session_state.get("DRAFT_TEXT", "")
edited_text = st.text_area(
    "Edit directly as you wish",
    value=st.session_state.get("EDIT_DRAFT", original_text),
    height=400,
    key="EDIT_DRAFT",
)

prev_snapshot = st.session_state.get("_LAST_EDIT_SNAPSHOT", original_text)
if edited_text.strip() != prev_snapshot.strip():
    version_num = (st.session_state.get("EDIT_VERSION", 0) or 0) + 1
    st.session_state["EDIT_VERSION"] = version_num
    st.session_state["_LAST_EDIT_SNAPSHOT"] = edited_text
    try:
        save_letter(UID, sid, edited_text, kind=f"edit_v{version_num}")
    except Exception as e:
        print("Saving edit version failed:", e)
    try:
        upsert_final_and_metric(UID, sid, edited_text)
    except Exception as e:
        print("Autosave (upsert_final_and_metric) failed:", e)
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

st.markdown("### Tips for Your Resume 💡")
suggestions_text = st.session_state.get("SUGGESTIONS_TEXT", "")
if suggestions_text:
    st.markdown(suggestions_text)
else:
    st.info("No suggestions generated yet.")

reason = st.text_input("(optional) provide feedback to improve your next experience", key="feedback_reason")
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
                        "final_text": (final_info or {}).get("final_text", st.session_state.get("FINAL_TEXT", "")),
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
                        "final_text": (final_info or {}).get("final_text", st.session_state.get("FINAL_TEXT", "")),
                    },
                )
            except Exception as e:
                print("Logging feedback_submitted failed:", e)
            st.success("Noted. Saved internally.")
        else:
            st.info("Generate a draft first.")
