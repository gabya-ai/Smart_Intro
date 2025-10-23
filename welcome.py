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


# # welcome.py — show intro when signed-in, redirect only on first login or when not signed-in
# import urllib.parse as _u
# import streamlit as st
# from firebase_admin import auth as admin_auth, initialize_app, _apps
# from db_ops import ensure_user_profile

# st.set_page_config(page_title="Genie-Hi", page_icon="💌", layout="wide")
# # welcome.py
# import streamlit as st
# from urllib.parse import parse_qs, urlparse
# import firebase_init  # your Admin SDK init bound to genie-hi-front
# from firebase_admin import auth as admin_auth

# # ---- read query params (works across Streamlit versions) ----
# try:
#     qp = st.query_params  # newer Streamlit
#     id_token = qp.get("id_token", None)
# except Exception:
#     qp = st.experimental_get_query_params()  # older Streamlit
#     id_token = qp.get("id_token", [None])[0] if "id_token" in qp else None

# if "signed_in" not in st.session_state:
#     st.session_state.signed_in = False
#     st.session_state.uid = None

# # ---- verify token ONLY ONCE ----
# if not st.session_state.signed_in:
#     if not id_token:
#         st.info("Please sign in from the landing page.")
#         st.stop()
#     try:
#         decoded = admin_auth.verify_id_token(id_token)
#         st.session_state.signed_in = True
#         st.session_state.uid = decoded.get("uid")
#         # Clear the querystring so refreshes don't re-verify or loop
#         try:
#             st.experimental_set_query_params()
#         except Exception:
#             pass
#     except Exception as e:
#         st.error("Session invalid or expired. Please sign in again.")
#         st.stop()

# # ---- you're signed in; render app without further redirects ----
# st.success(f"Welcome, UID: {st.session_state.uid}")

# # Initialize Firebase Admin once
# if not _apps:
#     initialize_app()

# FRONTEND_HOST = "https://genie-hi-front.web.app/"
# CLOUD_RUN_ROOT = "https://genie-hi-770619956563.us-west1.run.app/"

# def _first(v):
#     return v[0] if isinstance(v, list) else v

# # --- Firestore heartbeat (forces a visible write on app start) ---
# import streamlit as st

# # Option A: direct Firestore write (bypasses your helper to prove the pipeline works)
# try:
#     from google.cloud import firestore as gcf
#     _client = gcf.Client()
#     print("DEBUG Firestore project =", _client.project)

#     # add a tiny doc so a top-level 'interaction_logs' collection appears
#     _client.collection("interaction_logs").add({
#         "uid": "debug-uid",
#         "session_id": "debug-session",
#         "event_type": "heartbeat",
#         "details": {"source": "welcome.py startup"},
#         "ts": gcf.SERVER_TIMESTAMP
#     })
#     print("DEBUG: direct heartbeat write attempted to 'interaction_logs'")
#     st.caption("✅ Firestore heartbeat attempted (welcome.py). Check 'interaction_logs'.")
# except Exception as e:
#     print("ERROR: direct heartbeat write failed:", e)
#     st.caption(f"❌ Firestore heartbeat failed: {e}")

# # Option B: also test your helper, if available
# try:
#     from db_ops import log_interaction
#     log_interaction(
#         uid="debug-uid",
#         session_id="debug-session",
#         event_type="heartbeat_via_helper",
#         payload={"source": "welcome.py startup via db_ops"}
#     )
#     print("DEBUG: helper heartbeat write attempted to 'interaction_logs'")
# except Exception as e:
#     print("WARN: helper log_interaction failed:", e)
# # --- end heartbeat ---


# # --- Read query params (supported API) ---
# params = st.query_params
# token = _first(params.get("id_token"))

# # --- Case 1: User just arrived with a token → verify, persist, and go to Cover Letter
# if token:
#     try:
#         decoded = admin_auth.verify_id_token(token)
#         user = {"uid": decoded["uid"], "email": decoded.get("email", "")}
#         st.session_state["user"] = user
#         ensure_user_profile(user["uid"], user["email"])

#         # NEW: persist the token in the URL so refresh doesn't force a round-trip
#         st.query_params["id_token"] = token
        
#         # st.switch_page("pages/1_Cover_Letter.py")
#         # st.stop()
#     except Exception as e:
#         st.error(f"Token invalid: {e}")

# # --- Case 2: Already signed in (session exists) → show Welcome intro (NO sign-in prompt)
# if "user" in st.session_state:
#     user = st.session_state["user"]
#     st.title("Welcome to Genie-Hi ✨")
#     st.caption(f"Signed in as **{user.get('email','')}**")

#     st.markdown(
#         """
#         Genie-Hi helps you craft tailored, authentic cover letters and outreach in your own voice.

#         **About me**  
#         Hi, I’m **Gabrielle (Gabby) Yang** — I built Genie-Hi to make job search writing faster and kinder.

#         • [LinkedIn](https://www.linkedin.com/in/gabrielle-yang/)  
#         • [Medium](https://medium.com/@gxyang13)
#         """,
#         unsafe_allow_html=False,
#     )

#     # Primary action: go to Cover Letter
#     # st.link_button("Open Cover Letter", "pages/1_Cover_Letter", type="primary")

#     # “Sign in” is disabled for signed-in users (visual cue only)
#     st.button("Sign in (already signed in)", disabled=True)

#     st.info("Tip: you can refresh the browser — your session will be renewed automatically, but your content will be lost.")

#     st.stop()

# # --- Case 3: Not signed in → round-trip to Hosting to refresh ID token, then land back here
# signin = f"{FRONTEND_HOST}?return={_u.quote(CLOUD_RUN_ROOT, safe='')}"
# st.markdown(
#     f"""
#     <meta http-equiv="refresh" content="0; url={signin}">
#     <div style="font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
#       Redirecting to sign-in to refresh your session…
#       <br/><br/>
#       If nothing happens, <a href="{signin}">click here</a>.
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

# welcome.py — router-only, no experimental_* APIs, uses meta refresh redirect
# import urllib.parse as _u
# import streamlit as st
# from firebase_admin import auth as admin_auth, initialize_app, _apps
# from db_ops import ensure_user_profile

# st.set_page_config(page_title="Genie-Hi", page_icon="💌", layout="wide")

# # Init Firebase Admin once
# if not _apps:
#     initialize_app()

# FRONTEND_HOST = "https://genie-hi-front.web.app/"
# CLOUD_RUN_ROOT = "https://genie-hi-770619956563.us-west1.run.app/"

# def _first(val):
#     return val[0] if isinstance(val, list) else val

# # --- Handle ?id_token or existing session ---
# token = _first(st.query_params.get("id_token"))

# if token:
#     try:
#         decoded = admin_auth.verify_id_token(token)
#         user = {"uid": decoded["uid"], "email": decoded.get("email", "")}
#         st.session_state["user"] = user
#         ensure_user_profile(user["uid"], user["email"])
#         st.switch_page("pages/1_Cover_Letter.py")
#         st.stop()
#     except Exception as e:
#         st.error(f"Token invalid: {e}")

# elif "user" in st.session_state:
#     st.switch_page("pages/1_Cover_Letter.py")
#     st.stop()

# # --- No token/session: silent round-trip to Hosting to refresh id_token ---
# signin = f"{FRONTEND_HOST}?return={_u.quote(CLOUD_RUN_ROOT, safe='')}"

# # Use a META refresh (reliable inside Streamlit) + a visible fallback link
# st.markdown(
#     f"""
#     <meta http-equiv="refresh" content="0; url={signin}">
#     <div style="font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
#       Redirecting to sign-in to refresh your session…
#       <br/><br/>
#       If nothing happens, <a href="{signin}">click here</a>.
#     </div>
#     """,
#     unsafe_allow_html=True,
# )


# # welcome.py — verify with Firebase Admin SDK and route to Cover Letter
# import os
# import streamlit as st
# from firebase_admin import auth as admin_auth, initialize_app, _apps
# from db_ops import ensure_user_profile

# st.set_page_config(page_title="Genie-Hi", page_icon="💌", layout="wide")

# # Init Firebase Admin once per process (works on Cloud Run & local with ADC)
# if not _apps:
#     initialize_app()

# FRONTEND_HOST = "https://genie-hi-front.web.app/"

# def _to_str(x):
#     # Streamlit can give list for repeated query params
#     if isinstance(x, list): 
#         return x[0]
#     return x

# # --- Handle ?id_token or existing session ---
# token = _to_str(st.query_params.get("id_token"))

# if token:
#     try:
#         decoded = admin_auth.verify_id_token(token)   # <-- robust verifier
#         user = {"uid": decoded["uid"], "email": decoded.get("email", "")}
#         st.session_state["user"] = user
#         ensure_user_profile(user["uid"], user["email"])
#         st.switch_page("pages/1_Cover_Letter.py")
#         st.stop()
#     except Exception as e:
#         # Show the reason once, but fall through to the sign-in link
#         st.error(f"Token invalid: {e}")

# elif "user" in st.session_state:
#     st.switch_page("pages/1_Cover_Letter.py")
#     st.stop()

# # --- No token/session → auto-redirect to sign-in with return=back_here ---
# import urllib.parse as _u
# current_url = st.experimental_get_query_params()
# # Build the current full URL (root path works fine)
# return_to = "https://genie-hi-770619956563.us-west1.run.app/"

# signin = f"https://genie-hi-front.web.app/?return={_u.quote(return_to, safe='')}"
# st.markdown(
#     f"""
#     <script>
#       // silent redirect to Hosting so it refreshes id_token and sends us back
#       window.location.replace("{signin}");
#     </script>
#     """,
#     unsafe_allow_html=True
# )

# # --- No token/session → send user to web sign-in
# # st.markdown(
# #     f"""
# #     ### Please sign in first
# #     [Go to Sign-In Page]({FRONTEND_HOST})
# #     """
# # )
