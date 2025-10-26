import os
import pathlib
import streamlit as st

# Firebase Admin
import firebase_admin
from firebase_admin import credentials, auth

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="Genie-Hi", page_icon="💫", layout="centered")

st.markdown(
    """
    <style>
    body { background-color: #f7f8fc; font-family: Inter, system-ui, -apple-system, Segoe UI, sans-serif; }
    .main-title { text-align: center; font-size: 2rem; font-weight: 600; color: #1c1c28; margin-top: 0.5em; }
    .sub-title { text-align: center; color: #5a5a73; margin-bottom: 1.5em; }
    .card { background: #fff; border-radius: 18px; padding: 22px; box-shadow: 0 10px 28px rgba(0,0,0,0.06); }
    </style>
    """,
    unsafe_allow_html=True
)

# st.markdown("<h1 class='main-title'>Welcome to Genie-Hi ✨</h1>", unsafe_allow_html=True)
# st.markdown("<p class='sub-title'>Your personal career assistant to craft authentic messages.</p>", unsafe_allow_html=True)

# -------------------------------
# Config: URLs and Credentials
# -------------------------------
HOSTING_URL = os.environ.get("HOSTING_URL", "https://genie-hi-front.web.app")  # Firebase Hosting sign-in page
LOCAL_DEV = os.environ.get("LOCAL_DEV", "1")  # set to "1" for local, unset/0 for prod if you want
APP_RETURN_URL = os.environ.get(
    "APP_RETURN_URL",
    "http://localhost:8501" if LOCAL_DEV else "https://genie-hi-503651948869.us-west1.run.app"
)

# Path to service account JSON: env var wins, fallback to local file
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service-account-genie-hi-front.json")

def init_firebase_admin():
    """Initialize Firebase Admin. Prefer a JSON key if provided; otherwise use ADC on Cloud Run."""
    if firebase_admin._apps:
        return

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    try:
        if key_path:  # explicit key provided (local dev or if you really want a file)
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
        else:
            # No file → use ADC (Cloud Run / GCE / GKE). No special env needed.
            firebase_admin.initialize_app()
    except Exception as e:
        st.error(
            "Firebase Admin failed to initialize.\n\n"
            f"GOOGLE_APPLICATION_CREDENTIALS={key_path or '(unset: using ADC)'}\n\n"
            f"Error: {e}\n\n"
            "Fix options:\n"
            "• Preferred on Cloud Run: leave GOOGLE_APPLICATION_CREDENTIALS unset and rely on ADC.\n"
            "• Local dev: export GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/your-key.json"
        )
        st.stop()


# -------------------------------
# Session State
# -------------------------------
if "signed_in" not in st.session_state:
    st.session_state.signed_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user" not in st.session_state:
    st.session_state.user = None
if "id_token" not in st.session_state:
    st.session_state.id_token = None


# -------------------------------
# Read token from query params (if any)
# -------------------------------
def get_param(name: str):
    """Handle both Streamlit's new string return and any legacy list return."""
    val = st.query_params.get(name)
    if isinstance(val, list):
        return val[0] if val else None
    return val

id_token = get_param("id_token")

# -------------------------------
# Verify token if present
# -------------------------------
if id_token and not st.session_state.signed_in:
    try:
        init_firebase_admin()
        decoded = auth.verify_id_token(id_token)
        st.session_state.signed_in = True
        st.session_state.user_email = decoded.get("email") or "User"
        st.session_state.user = {
            "uid": decoded.get("uid"),
            "email": decoded.get("email", "User"),
        }
        st.session_state.id_token = id_token
        st.switch_page("pages/1_Cover_Letter.py")
        # Clean URL
        st.query_params.clear()
    except Exception as e:
        st.warning(f"Invalid or expired token. Please sign in again. ({e})")
        st.session_state.signed_in = False
        st.session_state.user = None
        st.session_state.id_token = None

# -------------------------------
# Not Signed In? Auto-redirect to Hosting sign-in page
# -------------------------------
if not st.session_state.signed_in and not id_token:
    signin_url = f"{HOSTING_URL}?return={APP_RETURN_URL}"
    # Instant redirect
    st.markdown(f'<meta http-equiv="refresh" content="0; url={signin_url}">', unsafe_allow_html=True)
    st.stop()

# -------------------------------
# Signed-in View
# -------------------------------
if st.session_state.signed_in:
    with st.container():

        st.title("Welcome to Genie-Hi ✨")
        st.caption(f"Signed in as **{st.session_state.user_email}**")

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

        # Primary action: go to Cover Letter
        # st.link_button("Open Cover Letter", "pages/1_Cover_Letter", type="primary")

        # “Sign in” is disabled for signed-in users (visual cue only)
        st.button("Sign in (already signed in)", disabled=True)

        st.info(
            "you can refresh the browser — your session will be renewed automatically, but your content will be lost."
        )

else:
    # Fallback (should rarely appear due to redirect)
    st.info("Please sign in to continue.")

