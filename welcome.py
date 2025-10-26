import os
import json
import streamlit as st

# Must be the first Streamlit call
st.set_page_config(page_title="Genie-Hi", page_icon="💫", layout="centered")

# Safe to import after page_config
import firebase_admin
from firebase_admin import credentials, auth
import streamlit.web.server.websocket_headers as st_ws
# -------------------------------
# Helpers: session-state with defaults
# -------------------------------
def ss_get(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

ss_get("user", None)
ss_get("user_email", None)
ss_get("id_token", None)
ss_get("signed_in", False)

# -------------------------------
# Firebase Admin init (ADC on Cloud Run; key locally if provided)
# -------------------------------
def init_firebase_admin():
    if firebase_admin._apps:
        return
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    try:
        if key_path:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()  # ADC / metadata
    except Exception as e:
        st.error(
            "Firebase Admin failed to initialize.\n\n"
            f"GOOGLE_APPLICATION_CREDENTIALS={key_path or '(unset: using ADC)'}\n\n"
            f"Error: {e}"
        )
        st.stop()

# -------------------------------
# Dev vs Prod URLs
# -------------------------------
LOCAL_DEV = os.environ.get("LOCAL_DEV", "0")
IS_LOCAL = LOCAL_DEV.lower() in ("1", "true", "yes")
HOSTING_URL = os.environ.get("HOSTING_URL", "https://genie-hi-front.web.app")
APP_RETURN_URL = os.environ.get(
    "APP_RETURN_URL",
    "http://localhost:8501" if IS_LOCAL else "https://genie-hi-503651948869.us-west1.run.app",
)

# -------------------------------
# Cookie helpers (built-in)
# -------------------------------
COOKIE_NAME = "gh_id_token"

def _raw_cookie_header() -> str:
    """Return the raw Cookie header safely across Streamlit versions."""
    try:
        # ✅ Preferred in Streamlit ≥1.37
        return getattr(st, "context").headers.get("Cookie", "")
    except Exception:
        # Fallback for older builds
        try:
            import streamlit.web.server.websocket_headers as st_ws
            return st_ws._get_websocket_headers().get("Cookie", "")
        except Exception:
            return ""
        
def get_cookie() -> str | None:
    """Read cookie value from headers."""
    cookies = _raw_cookie_header()
    for kv in cookies.split(";"):
        if kv.strip().startswith(f"{COOKIE_NAME}="):
            return kv.split("=", 1)[1].strip()
    return None


def set_cookie(token: str | None):
    """Write cookie via HTML/JS (works for all Streamlit versions)."""
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

# -------------------------------
# Try cookie restore first (for refresh durability)
# -------------------------------
def restore_user_from_cookie():
    token = get_cookie()
    if not token:
        return False
    try:
        init_firebase_admin()
        claims = auth.verify_id_token(token)
        st.session_state["user"] = {"uid": claims.get("uid"), "email": claims.get("email")}
        st.session_state["user_email"] = claims.get("email")
        st.session_state["id_token"] = token
        st.session_state["signed_in"] = True
        return True
    except Exception:
        # expired/invalid → clear
        set_cookie(None)
        st.session_state["user"] = None
        st.session_state["user_email"] = None
        st.session_state["id_token"] = None
        st.session_state["signed_in"] = False
        return False

restore_user_from_cookie()

# -------------------------------
# Read token from query params (first-time sign-in return)
# -------------------------------
def qp(name: str):
    val = st.query_params.get(name)
    if isinstance(val, list):
        return val[0] if val else None
    return val

id_token = qp("id_token")

if id_token and not st.session_state.get("signed_in", False):
    try:
        init_firebase_admin()
        decoded = auth.verify_id_token(id_token)

        # Persist for future refreshes
        set_cookie(id_token)

        # Hydrate session
        st.session_state["signed_in"] = True
        st.session_state["user_email"] = decoded.get("email") or "User"
        st.session_state["user"] = {"uid": decoded.get("uid"), "email": decoded.get("email", "User")}
        st.session_state["id_token"] = id_token

        # Clean URL and go to Cover Letter
        st.query_params.clear()
        st.switch_page("pages/1_Cover_Letter.py")
    except Exception as e:
        st.warning(f"Invalid or expired token. Please sign in again. ({e})")
        # fall through to sign-in redirect below

# -------------------------------
# If not signed in (and no token), bounce to Hosting sign-in
# -------------------------------
if not st.session_state.get("signed_in", False) and not id_token:
    signin_url = f"{HOSTING_URL}?return={APP_RETURN_URL}"
    # hard redirect via meta refresh (so browser location actually changes)
    st.markdown(f'<meta http-equiv="refresh" content="0; url={signin_url}">', unsafe_allow_html=True)
    st.stop()

# -------------------------------
# Signed-in landing
# -------------------------------
st.title("Welcome to Genie-Hi ✨")
st.caption(f"Signed in as **{st.session_state['user_email']}**")

st.markdown(
            """
            Genie-Hi helps you craft tailored, authentic cover letters and outreach in your own voice.

            **About me**  
            Hi, I’m **Gabrielle (Gabby) Yang** — I built Genie-Hi to make job search writing faster and kinder.

            • [LinkedIn](https://www.linkedin.com/in/gabrielle-yang/)  
            • [Medium](https://medium.com/@gxyang13)
            """,
            unsafe_allow_html=False,
        )
st.info("You can refresh the browser — your sign-in will persist.")
