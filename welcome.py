# welcome.py — show intro when signed-in, redirect only on first login or when not signed-in
import urllib.parse as _u
import streamlit as st
from firebase_admin import auth as admin_auth, initialize_app, _apps
from db_ops import ensure_user_profile

st.set_page_config(page_title="Genie-Hi", page_icon="💌", layout="wide")

# Initialize Firebase Admin once
if not _apps:
    initialize_app()

FRONTEND_HOST = "https://genie-hi-front.web.app/"
CLOUD_RUN_ROOT = "https://genie-hi-770619956563.us-west1.run.app/"

def _first(v):
    return v[0] if isinstance(v, list) else v

# --- Read query params (supported API) ---
params = st.query_params
token = _first(params.get("id_token"))

# --- Case 1: User just arrived with a token → verify, persist, and go to Cover Letter
if token:
    try:
        decoded = admin_auth.verify_id_token(token)
        user = {"uid": decoded["uid"], "email": decoded.get("email", "")}
        st.session_state["user"] = user
        ensure_user_profile(user["uid"], user["email"])

        # NEW: persist the token in the URL so refresh doesn't force a round-trip
        st.query_params["id_token"] = token
        
        # st.switch_page("pages/1_Cover_Letter.py")
        # st.stop()
    except Exception as e:
        st.error(f"Token invalid: {e}")

# --- Case 2: Already signed in (session exists) → show Welcome intro (NO sign-in prompt)
if "user" in st.session_state:
    user = st.session_state["user"]
    st.title("Welcome to Genie-Hi ✨")
    st.caption(f"Signed in as **{user.get('email','')}**")

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

    st.info("Tip: you can refresh the browser — your session will be renewed automatically, but your content will be lost.")

    st.stop()

# --- Case 3: Not signed in → round-trip to Hosting to refresh ID token, then land back here
signin = f"{FRONTEND_HOST}?return={_u.quote(CLOUD_RUN_ROOT, safe='')}"
st.markdown(
    f"""
    <meta http-equiv="refresh" content="0; url={signin}">
    <div style="font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
      Redirecting to sign-in to refresh your session…
      <br/><br/>
      If nothing happens, <a href="{signin}">click here</a>.
    </div>
    """,
    unsafe_allow_html=True,
)

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
