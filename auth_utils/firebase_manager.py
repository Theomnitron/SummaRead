# auth_utils/firebase_manager.py
import streamlit as st
import logging
import traceback

from PIL import Image

# Firebase admin imports
import firebase_admin
from firebase_admin import credentials, auth, firestore as admin_firestore

# Optional libs
import requests
from google.oauth2 import service_account
from google.cloud import firestore as gc_firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_service_account_info():
    """Read service account info from st.secrets and normalise the private key newlines."""
    try:
        fb = st.secrets["firebase"]
    except Exception as e:
        raise RuntimeError("Missing st.secrets['firebase'] — add your Firebase service account to .streamlit/secrets.toml") from e

    # required keys (adjust if your secret uses other field names)
    sa = {
        "type": fb.get("type"),
        "project_id": fb.get("project_id"),
        "private_key_id": fb.get("private_key_id"),
        "private_key": fb.get("private_key"),
        "client_email": fb.get("client_email"),
        "client_id": fb.get("client_id"),
        "auth_uri": fb.get("auth_uri"),
        "token_uri": fb.get("token_uri"),
        "auth_provider_x509_cert_url": fb.get("auth_provider_x509_cert_url"),
        "client_x509_cert_url": fb.get("client_x509_cert_url"),
        "universe_domain": fb.get("universe_domain")
    }

    # If private_key was stored with literal "\n" escapes, replace them.
    if sa["private_key"] and "\\n" in sa["private_key"]:
        sa["private_key"] = sa["private_key"].replace("\\n", "\n")

    return sa


@st.cache_resource
def get_firebase_app():
    """
    Initialize (or return) a firebase_admin.App.
    We create a named app and return it; callers should pass this app to auth calls.
    """
    try:
        # If an app already exists in this process, reuse the first available app object.
        if firebase_admin._apps:
            try:
                # try default get_app
                return firebase_admin.get_app()
            except Exception:
                # fallback to returning an existing app object
                return list(firebase_admin._apps.values())[0]

        service_account_info = _load_service_account_info()
        cred = credentials.Certificate(service_account_info)

        # initialize a named app (we will pass this app explicitly to auth calls)
        app = firebase_admin.initialize_app(cred, name="streamlit_app")
        logger.info("Initialized firebase app (streamlit_app)")
        return app

    except Exception as e:
        logger.error("Failed to initialize Firebase app: %s", str(e))
        logger.debug(traceback.format_exc())
        # surface friendly error to Streamlit
        st.error("Firebase initialization failed. Check your .streamlit/secrets.toml and restart the app.")
        st.stop()


@st.cache_resource
def get_firestore_db():
    """
    Return a Firestore client bound to the firebase app. Use firebase_admin's firestore client.
    This is cached per Streamlit session.
    """
    try:
        app = get_firebase_app()
        # firebase_admin's firestore client uses the same credentials and app
        db = admin_firestore.client(app=app)
        return db
    except Exception as e:
        # Fallback: try google.cloud.firestore with service account credentials
        logger.warning("firebase_admin.firestore.client failed, trying google.cloud.firestore fallback: %s", e)
        try:
            sa = _load_service_account_info()
            creds = service_account.Credentials.from_service_account_info(sa)
            db = gc_firestore.Client(project=sa["project_id"], credentials=creds)
            return db
        except Exception as e2:
            logger.error("Failed to initialize Firestore client: %s", e2)
            st.error("Failed to initialize Firestore client. Check your secrets and packages.")
            st.stop()





# --- Auth functions ---
def register_user(email: str, password: str, display_name: str = None):
    """
    Create a Firebase Authentication user (Admin SDK) and create a Firestore profile doc.
    Returns dict: {"success": bool, "message": str}
    """
    try:
        app = get_firebase_app()
        logger.info("Creating user: %s", email)

        # create user, explicitly passing the app
        user = auth.create_user(email=email, password=password, display_name=display_name, app=app)

        # prepare profile and save to firestore
        db = get_firestore_db()
        profile_data = {
            "email": user.email,
            "username": display_name if display_name else user.email.split("@")[0],
            "created_at": admin_firestore.SERVER_TIMESTAMP,
            "last_login": admin_firestore.SERVER_TIMESTAMP,
        }
        db.collection("users").document(user.uid).set(profile_data)

        # update session
        st.session_state.logged_in = True
        st.session_state.user_info = {"email": user.email, "uid": user.uid, "display_name": display_name}
        st.session_state.user_profile_data = profile_data

        return {"success": True, "message": "Registration successful!"}

    except Exception as e:
        logger.exception("register_user error")
        return {"success": False, "message": f"Unexpected error during registration: {e}"}


def login_user(email: str, password: str):
    """
    Log a user in.
    If you put your Firebase Web API key in secrets.toml (firebase.api_key),
    this function will call the REST signInWithPassword endpoint and verify the password.
    Otherwise it falls back to "user exists" check (Admin SDK cannot verify password).
    """
    try:
        app = get_firebase_app()
        fb = st.secrets.get("firebase", {})
        api_key = fb.get("api_key") or fb.get("firebase_api_key") or fb.get("web_api_key")

        if api_key:
            # Use Firebase Auth REST API to verify credentials
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
            payload = {"email": email, "password": password, "returnSecureToken": True}
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                try:
                    err = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    err = resp.text
                return {"success": False, "message": f"Authentication failed: {err}"}

            data = resp.json()
            uid = data.get("localId")
            # fetch user & profile
            user = auth.get_user(uid, app=app)
            db = get_firestore_db()
            profile_doc = db.collection("users").document(uid).get()
            profile = profile_doc.to_dict() if profile_doc.exists else {}

            st.session_state.logged_in = True
            st.session_state.user_info = {"email": user.email, "uid": user.uid, "display_name": user.display_name}
            st.session_state.user_profile_data = profile

            db.collection("users").document(uid).update({"last_login": admin_firestore.SERVER_TIMESTAMP})
            return {"success": True, "message": "Login successful!"}

        else:
            # Fallback: only check that the user exists (no password verification)
            user = auth.get_user_by_email(email, app=app)
            db = get_firestore_db()
            profile_doc = db.collection("users").document(user.uid).get()
            profile = profile_doc.to_dict() if profile_doc.exists else {}

            st.session_state.logged_in = True
            st.session_state.user_info = {"email": user.email, "uid": user.uid, "display_name": user.display_name}
            st.session_state.user_profile_data = profile

            db.collection("users").document(user.uid).update({"last_login": admin_firestore.SERVER_TIMESTAMP})
            return {
                "success": True,
                "message": "Login successful (note: password was not verified because firebase.api_key is not set)."
            }

    except Exception as e:
        logger.exception("login_user error")
        return {"success": False, "message": f"Unexpected error during login: {e}"}


def logout_user():
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.user_profile_data = None
    return {"success": True, "message": "Logged out successfully"}

# --- UI helper ---
def render_sidebar_profile():
    
    # --- Session defaults ---
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "user_profile_data" not in st.session_state:
        st.session_state.user_profile_data = None


    # --- Streamlit Configuration ---
    logo = 'logo/summaread_logo1.png'
    full_logo = 'logo/summaread_full_logo.png'

    logo_img = Image.open(logo)
    full_logo_img = Image.open(full_logo)

    st.set_page_config(
        page_icon= logo_img,
    )

    st.logo(
        image= full_logo_img,
        link= 'https://selar.com/showlove/tolumichael',
        icon_image= logo_img
    )

    with st.sidebar:

        # ONLY ADDED: Insert the global CSS makeover here
        st.markdown('''
        <style>
        /* Base Streamlit overrides to hide default elements and ensure global font/color */
        .stMainMenu, .st-emotion-cache-weq6zh.em9zgd017, #root > div:nth-child(1) > div > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi8 > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi5 > div:nth-child(1) > div > div.st-emotion-cache-f1g69q.e1nzilvr4 > div:nth-child(1) {
            visibility: hidden;
            height: 0px; /* Also collapse height if visibility is hidden */
            overflow: hidden;
        }
        /* Your existing img border-radius */
        img {
            border-radius: 15px;
        }

        /* --- GLOBAL CSS MAKEOVER --- */

        /* General Body Background (from config.toml base="dark" + custom background) */
        body {
            background-color: #1A1A1A; /* Ensure background is very dark */
            color: #FAFAFA; /* Light text color */
            font-family: 'Inter', sans-serif; /* A modern sans-serif font */
            line-height: 1.6;
            letter-spacing: 0.5px;
        }


        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #222222; /* Different shade of dark for sidebar */
            border-radius: 0 15px 15px 0; /* Rounded right corners */
            box-shadow: 5px 5px 15px rgba(0,0,0,0.5);
            width: 210px !important;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 12px; /* Curved borders */
            background: linear-gradient(to right, #2196F3, #0D47A1); /* Blue gradient */
            color: white; /* Text color */
            font-family: Inter;
            padding: 10px 20px;
            border: none;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3); /* Subtle shadow */
            transition: all 0.3s ease; /* Smooth transitions */
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton > button:hover {
            background: linear-gradient(to right, #0D47A1, #2196F3); /* Reverse gradient on hover */
            box-shadow: 4px 4px 10px rgba(0,0,0,0.5); /* Stronger shadow on hover */
            transform: translateY(-2px); /* Slight lift */
        }
        .stButton > button:active {
            background: #0A3D62; /* Even darker blue on click */
            transform: translateY(0); /* Press down effect */
            box-shadow: inset 1px 1px 3px rgba(0,0,0,0.5);
        }

        /* Text Inputs & Text Areas */
        /* Targeting the actual input/textarea elements within Streamlit's wrappers */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 1px solid #444; /* Darker border for dark theme */
            box-shadow: inset 1px 1px 3px rgba(0,0,0,0.2);
            background-color: #333; /* Slightly lighter than secondary background */
            color: #FAFAFA;
            transition: all 0.3s ease;
            padding: 10px 15px; /* More padding for text inputs */
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #2196F3; /* Blue border on focus */
            box-shadow: 0 0 5px #2196F3, inset 1px 1px 3px rgba(0,0,0,0.2); /* Blue glow on focus */
            outline: none; /* Remove default outline */
        }

        /* Placeholder Text */
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #999; /* Muted color for placeholders */
            opacity: 0.7;
        }

        /* Selectboxes */
        .stSelectbox > div > div { /* Targets the main visible part of the selectbox */
            border-radius: 8px;
            background-color: #333; /* Consistent background */
            border: 1px solid #444;
            box-shadow: inset 1px 1px 3px rgba(0,0,0,0.2);
            color: #FAFAFA;
            transition: all 0.3s ease;
        }
        .stSelectbox > div > div:focus-within { /* When any element inside is focused */
            border-color: #2196F3;
            box-shadow: 0 0 5px #2196F3, inset 1px 1px 3px rgba(0,0,0,0.2);
            outline: none;
        }
        /* Style the dropdown arrow */
        .stSelectbox [data-testid="stSelectboxDropdownArrow"] {
            color: #2196F3; /* Blue arrow */
        }
        /* Style the actual dropdown options */
        div[data-baseweb="popover"] div[role="listbox"] {
            background-color: #333; /* Dark background for dropdown options */
            color: #FAFAFA;
            border-radius: 8px;
            border: 1px solid #444;
        }
        div[data-baseweb="popover"] div[role="option"] {
            color: #FAFAFA;
        }
        div[data-baseweb="popover"] div[role="option"]:hover {
            background-color: #2196F3 !important; /* Blue on hover for options */
            color: white !important;
        }


        /* Tabs */
        .stTabs [data-baseweb="tab-list"] button {
            border-radius: 8px 8px 0 0; /* Rounded top corners */
            background-color: #2A2A2A; /* Default tab background */
            color: #BBB; /* Default text color */
            padding: 10px 15px;
            margin-right: 5px;
            border: 1px solid #444;
            border-bottom: none; /* No bottom border */
            transition: all 0.3s ease;
            font-weight: normal;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            background-color: #2196F3; /* Blue background for active tab */
            color: white;
            font-weight: bold;
            border-color: #2196F3;
            box-shadow: 0 -2px 10px rgba(33,150,243,0.5); /* Blue glow on active tab */
        }
        .stTabs [data-baseweb="tab-list"] button:hover:not([aria-selected="true"]) {
            background-color: #3A3A3A; /* Slightly lighten inactive tabs on hover */
        }
        /* Style the content area of the tabs */
        .stTabs [data-baseweb="tab-panel"] {
            background-color: #2A2A2A; /* Match secondary background */
            border-radius: 0 0 15px 15px; /* Rounded bottom corners */
            padding: 20px;
            border: 1px solid #444;
            border-top: none; /* No top border */
            box-shadow: 5px 5px 15px rgba(0,0,0,0.5);
        }
        /* Specific styling for summary components - keep Open-Dyslexic and ensure text color */
        .heading-summary {
            font-family: 'Open-Dyslexic', sans-serif !important;
            font-size: 28px !important;
            font-weight: 700;
            text-align: center;
            color: #FAFAFA; /* Explicitly set to ensure consistency */
            text-transform: capitalize;
        }
        .body-summary {
            font-family: 'Open-Dyslexic', sans-serif !important;
            font-size: 16px !important;
            line-height: 2rem;
            color: #FAFAFA; /* Explicitly set to ensure consistency */
            letter-spacing: 0.5px;
        }
        .points{
            font-family: 'Open-Dyslexic', sans-serif !important;
            font-size: 20px !important;
            color: #FAFAFA; /* Explicitly set to ensure consistency */
        }
        .outline-summary {
            font-family: 'Open-Dyslexic', sans-serif !important;
            font-size: 16px !important;
            padding-left: 25px;
            line-height: 1.5rem;
            color: #FAFAFA; /* Explicitly set to ensure consistency */
            letter-spacing: 0.5px;
        }

        /* General Streamlit Status Messages (st.success, st.info, st.error) */
        /* These classes might need dynamic inspection, but these are common ones */
        .st-emotion-cache-1f893l.e1f1d6z61 { /* General container for message */
            border-radius: 8px;
            padding: 10px 15px;
            margin: 10px 0;
            background-color: #333; /* Consistent dark background for messages */
            color: #FAFAFA; /* Light text */
        }
        /* Overrides for specific message types to retain Streamlit's color hints */
        div[data-testid="stStatusWidget"] [data-testid="stMarkdownContainer"] p {
            color: inherit !important; /* Ensure text color is inherited */
        }
        div[data-testid="stStatusWidget"] .stAlert {
            background-color: transparent !important; /* Let the container handle background */
            border: none !important; /* Remove default alert border */
        }
        div[data-testid="stStatusWidget"] svg { /* Targeting the icon */
            filter: brightness(1.5); /* Make icons brighter on dark theme */
        }
        
        /* Fixed footer styling (from 3_reader.py) - KEPT UNTOUCHED */
        .fixed-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(0, 0, 0, 0); /* Still transparent or very subtle */
            padding-left: 15px;
            padding-right: 15px;
            margin-bottom: 40px;
            border-radius: 2rem;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0);
            z-index: 1000;
        }
        </style>
        ''', unsafe_allow_html= True)

        if st.session_state.logged_in:
            user = st.session_state.user_info or {}
            profile = st.session_state.user_profile_data or {}
            st.write(f"**Welcome, {profile.get('username', user.get('email',''))}!**")
            st.write(f"Email: {user.get('email','-')}")
            if st.button("Logout"):
                logout_user()
                st.success("Logged out")
                # send user back to login page
                st.session_state.page = "Login"
                st.rerun()
        else:
            st.info("Please log in to access all features")
            if st.button("Login/Register"):
                st.session_state.page = "Login"
                # switch to your auth page (adjust if your page path/name differs)
                st.switch_page("pages/1_Profile.py")
            # Donate (PRESERVED - NO CHANGES)
        st.markdown(
            """
            <style>
                .coffee {
            }
            </style>
            <a href="https://selar.com/showlove/tolumichael" target="_blank">
                <img class='coffee' src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
            </a>
            """,
            unsafe_allow_html=True,
        )

