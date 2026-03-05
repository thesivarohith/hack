import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import streamlit.components.v1 as components
from streamlit_calendar import calendar
from datetime import date
import os

# -----------------------------------------------------------------------------
# 1. CONFIG & CSS
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FocusFlow")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ========== MATERIAL DESIGN FOUNDATION ========== */
    :root {
        --md-primary: #1A73E8;
        --md-primary-dark: #1557B0;
        --md-elevation-1: 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15);
        --md-elevation-2: 0 1px 2px 0 rgba(60,64,67,.3), 0 2px 6px 2px rgba(60,64,67,.15);
        --md-elevation-3: 0 4px 8px 3px rgba(60,64,67,.15), 0 1px 3px rgba(60,64,67,.3);
        --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
        --radius-md: 8px;
    }
    
    html { scroll-behavior: smooth; -webkit-font-smoothing: antialiased; }
    
    /* Global Reset & Fonts */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937;
        background-color: #FAFAFA;
    }
    
    /* Material Design Button Enhancements */
    .stButton > button {
        box-shadow: var(--md-elevation-2) !important;
        transition: all var(--transition-fast) !important;
        border-radius: var(--radius-md) !important;
    }
    .stButton > button:hover {
        box-shadow: var(--md-elevation-3) !important;
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Smooth Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage { animation: fadeInUp var(--transition-normal) ease-out; }
    
    /* Touch-Friendly Mobile */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        body { font-size: 16px; }
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
    }


    /* Input Styling for 'Exact Replica' look on Timer */
    div[data-testid="stNumberInput"] {
        width: auto;
        display: flex;
        justify-content: center;
    }
    /* Target the inner input specifically and ensure parents don't clip */
    div[data-testid="stNumberInput"] > div {
        border: none !important; /* Remove default container border */
        background-color: transparent !important;
        box-shadow: none !important;
        height: auto !important; /* Allow growing */
        padding: 0 !important;
    }
    div[data-testid="stNumberInput"] input {
        text-align: center;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        height: 80px !important;
        width: 80px !important;
        padding: 0 !important;
        margin: 0 !important;
        
        background-color: white !important;
        border: 2px solid #374151 !important;
        border-radius: 8px !important;
        color: #111827 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    /* Fix the colon vertically */
    .timer-colon {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-top: 0px; /* Removed offset */
        line-height: 80px; /* Match input height for centering */
        color: #111827;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* Hide number input arrows/spinners */
    div[data-testid="stNumberInput"] button {
        display: none !important;
    }
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    
    /* Hide uploaded file list in the uploader widget */
    section[data-testid="stFileUploader"] section[data-testid="stFileUploaderFile"] {
        display: none !important;
    }
    small { display: none !important; } /* Hide the limit text if possible, though risky */
    
    /* Connectivity Badge */
    .status-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        color: white;
    }
    .online { background-color: #22c55e; }
    .offline { background-color: #ef4444; }

    /* Custom Card via Border Container */
    /* We will use st.container(border=True) and let it be default styled or override if needed */


    /* --- COMPONENT STYLES --- */
    
    /* Card/Container Style */
    .custom-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
        border: 1px solid #E5E7EB;
    }

    /* Headings */
    h1, h2, h3 {
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
        padding: 0;
    }
    h3 { font-size: 1.25rem; }
    h4 { font-size: 1.1rem; color: #374151; font-weight: 600; }

    /* --- CONTROL CENTER (LEFT) --- */
    
    /* Timer Display */
    .timer-display {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
    .timer-box {
        background: white;
        border: 2px solid #374151;
        border-radius: 8px;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .timer-dots {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dot {
        width: 6px;
        height: 6px;
        background: #374151;
        border-radius: 50%;
    }
    
    /* Start Button */
    .stButton button {
        border-radius: 9999px !important; /* Pill shape */
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s;
    }
    /* Specific class targetting might be tricky in pure Streamlit CSS injection without parent ID,
       so we rely on order or button hierarchy in the python code usage. */
    
    /* Sources */
    .source-item {
        display: flex;
        align-items: center;
        padding: 10px;
        background: #F3F4F6;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #4B5563;
        font-size: 0.9rem;
        font-weight: 500;
    }
    .source-icon {
        margin-right: 10px;
        font-size: 1.2rem;
    }
    
    /* --- WORKSPACE (MIDDLE) --- */
    .article-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.3;
    }
    .article-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .citation {
        color: #2563EB;
        font-size: 0.8rem;
        vertical-align: super;
        cursor: pointer;
    }

    /* --- SCHEDULER (RIGHT) --- */
    .calendar-wrapper {
        font-size: 0.8rem;
    }
    
    /* Topic Card */
    .topic-card {
        border-bottom: 1px solid #E5E7EB;
        padding: 12px 0;
    }
    .topic-card:last-child { border-bottom: none; }
    
    .topic-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
    }
    
    /* --- CALENDAR HORIZONTAL FORCE --- */
    /* CSS cannot penetrate the iframe, so we rely on component options now. */
    /* Keeping the container clean */
    /* Fix Calendar Title Size for sidebar */
    .fc-toolbar-title {
        font-size: 1.1rem !important; /* Smaller size to fit sidebar */
        white-space: normal !important; /* Allow wrapping if needed? Or shrink more */
    }
    @media (max-width: 1400px) {
        .fc-toolbar-title {
            font-size: 0.9rem !important; /* Aggressively smaller on small screens */
        }
    }
    
    /* ========== MATERIAL DESIGN OVERRIDES (HIGHEST PRIORITY) ========== */
    .stButton > button {
        background: #1A73E8 !important;
        color: white !important;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,.3), 0 2px 6px 2px rgba(60,64,67,.15) !important;
        transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1) !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 10px 24px !important;
    }
    
    .stButton > button:hover {
        background: #1557B0 !important;
        box-shadow: 0 4px 8px 3px rgba(60,64,67,.15), 0 1px 3px rgba(60,64,67,.3) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# Backend URL
API_URL = "http://localhost:8000"

# ========== FIREBASE AUTH CONFIG ==========
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_AUTH_ENABLED = bool(FIREBASE_API_KEY and FIREBASE_PROJECT_ID)

# ========== LANDING PAGE / LOGIN SCREEN ==========
_is_authenticated = "firebase_token" in st.session_state or "local_bypass" in st.session_state

if not _is_authenticated:
    # Check if token was passed back from the login component
    params = st.query_params
    if "fb_token" in params and "fb_uid" in params:
        st.session_state["firebase_token"] = params["fb_token"]
        st.session_state["user_info"] = {
            "uid": params.get("fb_uid", ""),
            "email": params.get("fb_email", ""),
            "displayName": params.get("fb_name", "User"),
            "photoURL": params.get("fb_photo", ""),
        }
        # Clear query params after reading
        st.query_params.clear()
        st.rerun()
    else:
        # Show login screen
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;
                    min-height: 80vh; text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 0.25rem;">🎯</div>
            <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">FocusFlow</h1>
            <p style="color: #6B7280; font-size: 1.1rem; margin-bottom: 2rem;">AI-Powered Study Companion</p>
        </div>
        """, unsafe_allow_html=True)

        # ---- Native Streamlit Login Form (works in HuggingFace + everywhere) ----
        if "show_login_ui" not in st.session_state:
            st.session_state.show_login_ui = False
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"  # "login" or "signup"

        if not st.session_state.show_login_ui:
            col_l, col_mid, col_r = st.columns([2, 1, 2])
            with col_mid:
                if st.button("🔐 Log In / Sign Up", type="primary", use_container_width=True):
                    st.session_state.show_login_ui = True
                    st.rerun()
                if not FIREBASE_AUTH_ENABLED:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("▶ Continue without login", use_container_width=True):
                        st.session_state["local_bypass"] = True
                        st.rerun()
        else:
            col_l, col_mid, col_r = st.columns([1.5, 2, 1.5])
            with col_mid:
                # Toggle between Login and Sign Up
                tab_login, tab_signup = st.tabs(["🔑 Log In", "📝 Sign Up"])

                def _firebase_email_auth(email, password, is_signup=False):
                    """Call Firebase REST API for email/password auth."""
                    endpoint = "signUp" if is_signup else "signInWithPassword"
                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{endpoint}?key={FIREBASE_API_KEY}"
                    resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
                    return resp.json()

                with tab_login:
                    with st.form("login_form"):
                        email = st.text_input("📧 Email", placeholder="you@example.com")
                        password = st.text_input("🔒 Password", type="password", placeholder="Your password")
                        submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
                        if submitted:
                            if not email or not password:
                                st.error("Please enter your email and password.")
                            elif not FIREBASE_AUTH_ENABLED:
                                st.error("Firebase not configured. Use 'Continue without login' instead.")
                            else:
                                try:
                                    result = _firebase_email_auth(email, password)
                                    if "idToken" in result:
                                        st.session_state["firebase_token"] = result["idToken"]
                                        st.session_state["user_info"] = {
                                            "uid": result.get("localId", ""),
                                            "email": result.get("email", ""),
                                            "displayName": result.get("displayName", email.split("@")[0]),
                                            "photoURL": result.get("photoURL", ""),
                                        }
                                        st.success("✅ Logged in!")
                                        st.rerun()
                                    else:
                                        err = result.get("error", {}).get("message", "Login failed")
                                        st.error(f"❌ {err.replace('_', ' ').title()}")
                                except Exception as e:
                                    st.error(f"Connection error: {e}")

                    if FIREBASE_AUTH_ENABLED:
                        st.markdown("---")
                        st.markdown("**Or sign in with:**")
                        google_auth_url = f"https://{FIREBASE_PROJECT_ID}.firebaseapp.com/__/auth/handler"
                        st.markdown(
                            f'<a href="https://accounts.google.com/o/oauth2/auth?client_id=272558417680-web&redirect_uri=https://{FIREBASE_PROJECT_ID}.firebaseapp.com/__/auth/handler&response_type=code&scope=email+profile" target="_blank">'
                            f'<button style="width:100%;padding:10px;border:1px solid #dadce0;border-radius:8px;background:white;cursor:pointer;font-size:15px;font-weight:500;color:#3c4043;margin-bottom:8px;">'
                            f'<svg style="vertical-align:middle;margin-right:8px" width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>'
                            f'Sign in with Google</button></a>',
                            unsafe_allow_html=True
                        )

                with tab_signup:
                    with st.form("signup_form"):
                        new_email = st.text_input("📧 Email", placeholder="you@example.com", key="signup_email")
                        new_password = st.text_input("🔒 Password", type="password", placeholder="At least 6 characters", key="signup_pass")
                        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password", key="confirm_pass")
                        signup_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
                        if signup_submitted:
                            if not new_email or not new_password:
                                st.error("Please fill in all fields.")
                            elif new_password != confirm_password:
                                st.error("Passwords do not match.")
                            elif len(new_password) < 6:
                                st.error("Password must be at least 6 characters.")
                            elif not FIREBASE_AUTH_ENABLED:
                                st.error("Firebase not configured.")
                            else:
                                try:
                                    result = _firebase_email_auth(new_email, new_password, is_signup=True)
                                    if "idToken" in result:
                                        st.session_state["firebase_token"] = result["idToken"]
                                        st.session_state["user_info"] = {
                                            "uid": result.get("localId", ""),
                                            "email": result.get("email", ""),
                                            "displayName": new_email.split("@")[0],
                                            "photoURL": "",
                                        }
                                        st.success("✅ Account created! Welcome to FocusFlow!")
                                        st.rerun()
                                    else:
                                        err = result.get("error", {}).get("message", "Sign up failed")
                                        st.error(f"❌ {err.replace('_', ' ').title()}")
                                except Exception as e:
                                    st.error(f"Connection error: {e}")

        st.stop()  # Don't render the rest of the app

# Session State
if "timer_running" not in st.session_state: st.session_state.timer_running = False
if "expiry_time" not in st.session_state: st.session_state.expiry_time = None
if "time_left_m" not in st.session_state: st.session_state.time_left_m = 0
if "time_left_s" not in st.session_state: st.session_state.time_left_s = 0
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "mastery_data" not in st.session_state: st.session_state.mastery_data = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
if "expanded_topics" not in st.session_state: st.session_state.expanded_topics = set()
if "show_analytics" not in st.session_state: st.session_state.show_analytics = False
if "topic_scores" not in st.session_state: st.session_state.topic_scores = {}  # Track quiz performance by topic_id

if "app_config" not in st.session_state:
    try:
        resp = requests.get(f"{API_URL}/config", timeout=5)
        if resp.status_code == 200:
            st.session_state.app_config = resp.json()
        else:
            st.session_state.app_config = {"youtube_enabled": True}
    except Exception:
        st.session_state.app_config = {"youtube_enabled": True}

# Helper function to add auth headers to all API requests
def get_headers():
    """Get auth headers for API requests — uses Firebase token if available."""
    headers = {}
    if FIREBASE_AUTH_ENABLED and "firebase_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['firebase_token']}"
    return headers

# Focus Mode State
if "focus_mode" not in st.session_state: st.session_state.focus_mode = False
if "active_topic" not in st.session_state: st.session_state.active_topic = None

# PERSISTENCE: Load student profile on first load
if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = True
    try:
        resp = requests.get(f"{API_URL}/student/profile", headers=get_headers(), timeout=5)
        if resp.status_code == 200:
            profile = resp.json()
            
            # DEBUG: Show what we got
            plan_topics = profile.get("study_plan", {}).get("topics", [])
            quiz_history = profile.get("quiz_history", [])
            
            # Restore study plan if exists
            if plan_topics:
                st.session_state.study_plan = plan_topics
                st.toast(f"📚 Restored {len(plan_topics)} topics from previous session", icon="✅")
            else:
                st.session_state.study_plan = []
                # Don't show message for first-time users
            
            # Restore quiz scores
            if quiz_history:
                for quiz_record in quiz_history:
                    st.session_state.topic_scores[quiz_record["topic_id"]] = {
                        "topic_title": quiz_record.get("topic_title"),
                        "score": quiz_record["score"],
                        "total": quiz_record["total"],
                        "percentage": quiz_record["percentage"]
                    }
                st.toast(f"📊 Restored {len(quiz_history)} quiz results", icon="✅")
            
            # Restore mastery data
            if profile.get("mastery_tracker"):
                st.session_state.mastery_data = profile["mastery_tracker"]
            
            # ========== DATE-AWARE DAY PROGRESSION ==========
            from datetime import date
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")
            
            # Get stored current day and last access date
            current_study_day = profile.get("current_study_day", 1)
            last_access_date = profile.get("last_access_date", today_str)
            
            # Check if it's a new calendar day
            if last_access_date != today_str and st.session_state.study_plan:
                # Calculate how many days have passed
                from datetime import datetime
                last_date_obj = datetime.strptime(last_access_date, "%Y-%m-%d").date()
                days_passed = (today - last_date_obj).days
                
                if days_passed > 0:
                    # Advance to next day
                    current_study_day += days_passed
                    max_day = max([t.get("day", 1) for t in st.session_state.study_plan]) if st.session_state.study_plan else 1
                    current_study_day = min(current_study_day, max_day)  # Cap at max day
                    
                    # Auto-unlock topics for the new day
                    for topic in st.session_state.study_plan:
                        if topic.get("day") == current_study_day and topic.get("status") != "completed":
                            topic["status"] = "unlocked"
                    
                    # Update profile with new day and date
                    try:
                        requests.post(f"{API_URL}/student/save_progress", json={
                            "current_study_day": current_study_day,
                            "last_access_date": today_str
                        }, headers=get_headers(), timeout=5)
                        st.toast(f"📅 Advanced to Day {current_study_day}! New topics unlocked", icon="🎯")
                    except:
                        pass
            
            # Store current day in session state
            st.session_state.current_study_day = current_study_day

        else:
            st.session_state.study_plan = []
            st.error(f"Could not load profile: {resp.status_code}")
    except Exception as e:
        st.session_state.study_plan = []
        st.error(f"Could not connect to backend: {e}")
else:
    # Ensure study_plan exists even if profile load was skipped
    if "study_plan" not in st.session_state:
        st.session_state.study_plan = []
    # Default to day 1 if no profile loaded
    if "current_study_day" not in st.session_state:
        st.session_state.current_study_day = 1


def check_internet():
    """
    Checks for internet connectivity by pinging reliable hosts.
    try multiple to be sure.
    """
    keywords = ["google.com", "cloudflare.com", "github.com"]
    for host in keywords:
        try:
            requests.get(f"http://{host}", timeout=3)
            return True
        except:
            continue
    return False

# -----------------------------------------------------------------------------
# 2. ANALYTICS MODAL (Rendered at top if active)
# -----------------------------------------------------------------------------
if st.session_state.show_analytics:
    with st.container():
        st.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; padding: 2rem; border-radius: 16px; width: 80%; max-width: 800px; height: 80%; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 2rem;">
                    <h2>Performance Analytics</h2>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # We can't easily put Streamlit widgets INSIDE that pure HTML string div above.
        # But we can simulate a modal by clearing the main area or using st.dialog (New in 1.34+)
        # If st.dialog is available (it was in the previous app.py), we should use it.
        pass

def extract_subjects_and_topics():
    """
    Extract subjects from study plan topics.
    Returns: {subject_name: [topic_data_with_scores]}
    """
    import re
    subjects = {}
    for topic in st.session_state.study_plan:
        title = topic.get("title", "")
        
        # Remove "Day X:" prefix if present
        title_cleaned = re.sub(r'^Day\s+\d+:\s*', '', title)
        
        # Try to extract subject from remaining text
        # Look for patterns like "OOPS:" or "Manufacturing:" or just use first few words
        if ":" in title_cleaned:
            # Get first part before colon as subject
            subject = title_cleaned.split(":")[0].strip()
        elif " - " in title_cleaned:
            # Alternative separator
            subject = title_cleaned.split(" - ")[0].strip()
        else:
            # Use first 2-3 capitalized words as subject
            words = title_cleaned.split()
            # Take first 1-2 capitalized words as subject name
            subject_words = []
            for word in words[:3]:
                if word[0].isupper() or word.isupper():
                    subject_words.append(word)
                else:
                    break
            subject = " ".join(subject_words) if subject_words else "General"
        
        # Clean up subject name
        subject = subject.strip()
        if not subject or subject.startswith("Day"):
            subject = "General"
        
        if subject not in subjects:
            subjects[subject] = []
        
        # Add topic with its score data
        topic_data = {
            "title": title,
            "id": topic.get("id"),
            "status": topic.get("status", "locked"),
            "quiz_passed": topic.get("quiz_passed", False)
        }
        
        # Add score if available
        if topic.get("id") in st.session_state.topic_scores:
            topic_data["score_data"] = st.session_state.topic_scores[topic.get("id")]
        
        subjects[subject].append(topic_data)
    
    return subjects


@st.dialog("📊 Analytics Overview", width="large")
def show_analytics_dialog():
    subjects_data = extract_subjects_and_topics()
    
    if not subjects_data:
        st.info("📚 No subjects found. Create a study plan to see analytics.")
        return
    
    # Create dynamic tabs
    subject_names = list(subjects_data.keys())
    tabs = st.tabs(subject_names)
    
    for idx, subject_name in enumerate(subject_names):
        with tabs[idx]:
            topics = subjects_data[subject_name]
            
            # Calculate subject mastery
            completed_topics = [t for t in topics if t.get("status") == "completed"]
            total_topics = len(topics)
            completion_pct = (len(completed_topics) / total_topics * 100) if total_topics > 0 else 0
            
            # Calculate average score for topics with quiz data
            topics_with_scores = [t for t in topics if "score_data" in t]
            if topics_with_scores:
                avg_score = sum(t["score_data"]["percentage"] for t in topics_with_scores) / len(topics_with_scores)
            else:
                avg_score = 0
            
            # Display mastery header
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="font-size: 4rem; color: #111827; margin: 0;">{avg_score:.1f}%</h1>
                <p style="color: #6B7280; font-size: 1.2rem;">Overall Mastery</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Topics Completed", f"{len(completed_topics)}/{total_topics}")
                st.progress(completion_pct / 100)
            
            with col2:
                st.metric("Quizzes Taken", f"{len(topics_with_scores)}/{total_topics}")
                quiz_completion = (len(topics_with_scores) / total_topics * 100) if total_topics > 0 else 0
                st.progress(quiz_completion / 100)
            
            st.markdown("---")
            st.markdown("### 📈 Performance Breakdown")
            
            # Classify topics by performance
            strong = [t for t in topics_with_scores if t["score_data"]["percentage"] >= 75]
            moderate = [t for t in topics_with_scores if 50 <= t["score_data"]["percentage"] < 75]
            needs_work = [t for t in topics_with_scores if t["score_data"]["percentage"] < 50]
            
            # Display classifications
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 💚 Strong Topics")
                st.caption(f"{len(strong)} topic(s)")
                if strong:
                    for t in strong:
                        score_pct = t["score_data"]["percentage"]
                        score_str = f"{t['score_data']['score']}/{t['score_data']['total']}"
                        st.success(f"**{t['title']}**\n{score_pct:.0f}% ({score_str})")
                else:
                    st.info("No strong topics yet. Keep studying!")
            
            with col2:
                st.markdown("#### 🟡 Moderate Topics")
                st.caption(f"{len(moderate)} topic(s)")
                if moderate:
                    for t in moderate:
                        score_pct = t["score_data"]["percentage"]
                        score_str = f"{t['score_data']['score']}/{t['score_data']['total']}"
                        st.warning(f"**{t['title']}**\n{score_pct:.0f}% ({score_str})")
                else:
                    st.info("No moderate topics yet")
            
            with col3:
                st.markdown("#### 🔴 Needs Work")
                st.caption(f"{len(needs_work)} topic(s)")
                if needs_work:
                    for t in needs_work:
                        score_pct = t["score_data"]["percentage"]
                        score_str = f"{t['score_data']['score']}/{t['score_data']['total']}"
                        st.error(f"**{t['title']}**\n{score_pct:.0f}% ({score_str})")
                else:
                    st.info("Great! No topics need extra work")


# -----------------------------------------------------------------------------
# 3. QUIZ TO UNLOCK (Dialog)
# -----------------------------------------------------------------------------
@st.dialog("Topic Mastery Quiz")
def show_quiz_dialog(topic_id, topic_name):
    st.markdown(f"### Quiz for: {topic_name}")
    st.write("Complete this short quiz to prove mastery and unlock the next topic.")
    
    with st.form(key=f"quiz_form_{topic_id}"):
        # Quiz Questions (Demo)
        st.markdown("**1. What is the First Law of Thermodynamics?**")
        q1 = st.radio("Select the best answer:", [
            "Energy cannot be created or destroyed, only transformed.",
            "Entropy always increases.",
            "Heat flows from cold to hot.",
            "F = ma"
        ], key=f"q1_{topic_id}")
        
        st.markdown("**2. Which system type allows energy but not matter transfer?**")
        q2 = st.radio("Select the best answer:", [
            "Open System",
            "Closed System",
            "Isolated System",
            "Solar System"
        ], key=f"q2_{topic_id}")
        
        if st.form_submit_button("Submit Quiz"):
            score = 0
            if q1.startswith("Energy cannot"): score += 50
            if q2 == "Closed System": score += 50
            
            # Call backend
            try:
                payload = {"topic_id": topic_id, "quiz_score": score}
                resp = requests.post(f"{API_URL}/unlock_topic", json=payload, headers=get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        if data.get("next_topic_unlocked"):
                            st.balloons()
                            st.success(f"Score: {score}% - PASSED! Next topic unlocked.")
                        else:
                            st.warning(f"Score: {score}% - Keep studying! You need >60% to pass.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(data.get("message"))
                else:
                    st.error(f"Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

        st.markdown("**P** <span style='float:right; background:#d1d5db; color:white; padding:2px 8px; border-radius:99px; font-size:0.8rem'>N/A</span>", unsafe_allow_html=True)
        st.markdown("<p style='color:#4B5563; margin-top:10px'>--</p>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. QUIZ TO UNLOCK (Dialog)
# -----------------------------------------------------------------------------
@st.dialog("Topic Mastery Quiz")
def show_quiz_dialog(topic_id, topic_name):
    st.markdown(f"**Topic:** {topic_name}")
    st.markdown("To unlock the next topic, you must pass this quiz.")
    
    # Mock Question
    st.info("Question: What is the primary concept of this topic?")
    
    ans = st.radio("Select Answer:", ["Energy Conservation", "Wrong Answer 1", "Wrong Answer 2"], key=f"q_radio_{topic_id}")
    
    if st.button("Submit Answer", type="primary"):
        if ans == "Energy Conservation":
            st.balloons()
            st.success("Correct! Next topic unlocked.")
            
            # Update Mock State
            for i, t in enumerate(st.session_state.study_plan):
                if t["id"] == topic_id:
                    t["quiz_passed"] = True
                    # Unlock next
                    if i + 1 < len(st.session_state.study_plan):
                        st.session_state.study_plan[i+1]["status"] = "unlocked"
                    break
            
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("Incorrect. Try again.")

# (The previous tool usage showed show_quiz_dialog was inserted. I will target the end of it to insert Flashcards)
# Actually, let's just insert it before MAIN LAYOUT, which is clearer.

# -----------------------------------------------------------------------------
# 4. FLASHCARDS (Dialog)
# -----------------------------------------------------------------------------
@st.dialog("Topic Flashcards", width="large")
def show_flashcard_dialog(topic_id, topic_name):
    st.markdown(f"### Flashcards: {topic_name}")
    
    # Flashcard Data (Demo)
    flashcards = [
        {"q": "What is the First Law of Thermodynamics?", "a": "Energy cannot be created or destroyed, only transformed."},
        {"q": "Define Entropy.", "a": "A measure of the disorder or randomness in a system."},
        {"q": "What is an Isolated System?", "a": "A system that exchanges neither matter nor energy with its surroundings."}
    ]
    
    # Session State for this dialog interaction
    # Note: st.dialog reruns the function body on interaction.
    if "fc_index" not in st.session_state: st.session_state.fc_index = 0
    if "fc_flipped" not in st.session_state: st.session_state.fc_flipped = False
    
    # Navigation Limits
    current_idx = st.session_state.fc_index
    total = len(flashcards)
    
    if current_idx >= total:
        st.success("You've reviewed all cards!")
        if st.button("Restart"):
            st.session_state.fc_index = 0
            st.session_state.fc_flipped = False
            st.rerun()
        return

    card = flashcards[current_idx]
    
    # Progress
    st.progress((current_idx + 1) / total)
    st.caption(f"Card {current_idx + 1} of {total}")
    
    # Card UI
    content = card["a"] if st.session_state.fc_flipped else card["q"]
    bg_color = "#EFF6FF" if not st.session_state.fc_flipped else "#F0FDF4" # Blue (Question) -> Green (Answer)
    border_color = "#DBEAFE" if not st.session_state.fc_flipped else "#BBF7D0"
    label = "QUESTION" if not st.session_state.fc_flipped else "ANSWER"
    
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border: 2px solid {border_color};
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        min-height: 200px;
        display: flex; 
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <div style="font-size: 0.8rem; font-weight: 700; color: #6B7280; margin-bottom: 10px; letter-spacing: 1px;">{label}</div>
        <div style="font-size: 1.5rem; font-weight: 600; color: #1F2937;">{content}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Controls
    c1, c2 = st.columns(2)
    with c1:
        btn_text = "Show Answer" if not st.session_state.fc_flipped else "Show Question"
        if st.button(btn_text, use_container_width=True):
            st.session_state.fc_flipped = not st.session_state.fc_flipped
            st.rerun()
            
    with c2:
        if st.session_state.fc_flipped:
            if st.button("Next Card →", type="primary", use_container_width=True):
                st.session_state.fc_index += 1
                st.session_state.fc_flipped = False
                st.rerun()
        else:
             st.button("Next Card →", disabled=True, use_container_width=True) # Lock next until flipped? Or allow skipping. Let's lock to encourage reading.
# --- LAYOUT SWITCHER ---
if not st.session_state.focus_mode:
    # Standard 3-Column Layout
    left_col, mid_col, right_col = st.columns([0.25, 0.50, 0.25], gap="medium")
else:
    # Focus Mode Layout (2 Columns: Chat + Content)
    left_col, mid_col = st.columns([0.30, 0.70], gap="large")
    right_col = None # Not used in Focus Mode

# --- LEFT COLUMN: Control Center ---
# --- LEFT COLUMN: Control Center ---
if not st.session_state.focus_mode:
    with left_col:
        # ====== USER INFO & SIGN-OUT (Firebase) ======
        if FIREBASE_AUTH_ENABLED and "user_info" in st.session_state:
            user = st.session_state["user_info"]
            photo_html = ""
            if user.get("photoURL"):
                photo_html = f'<img src="{user["photoURL"]}" style="width:32px;height:32px;border-radius:50%;margin-right:8px;vertical-align:middle;"/>'
            st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom:12px; padding:8px 12px;
                        background:#F3F4F6; border-radius:8px; font-size:0.9rem;">
                {photo_html}
                <span style="font-weight:600; color:#374151;">{user.get('displayName', 'User')}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Sign Out", key="signout_btn", use_container_width=True):
                for key in ["firebase_token", "user_info", "profile_loaded", "study_plan",
                            "topic_scores", "mastery_data", "chat_history"]:
                    st.session_state.pop(key, None)
                st.rerun()
            st.markdown("---")

        st.markdown("### Control Center")
        
        # Timer Widget
        with st.container(border=True):
            st.markdown('<div style="text-align: center; font-weight: 600; color: #374151; margin-bottom: 10px;">Study Timer</div>', unsafe_allow_html=True)
            
            # Timer Logic
            total_seconds = (st.session_state.time_left_m * 60) + st.session_state.time_left_s
            
            if st.session_state.timer_running:
                # Check if time is up
                remaining = st.session_state.expiry_time - time.time()
                
                if remaining <= 0:
                    st.session_state.timer_running = False
                    st.session_state.expiry_time = None
                    st.session_state.time_left_m, st.session_state.time_left_s = 0, 0
                    st.balloons()
                    st.rerun()
                else:
                    # Render JS Timer (Non-blocking)
                    
                    # We need to inject the SAME styles to match the look.
                    # Since components run in iframe, we copy the CSS.
                    m, s = divmod(int(remaining), 60)
                    
                    html_code = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                        body {{
                            font-family: 'Inter', sans-serif;
                            margin: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            background: transparent;
                            height: 100px; /* specific height */
                        }}
                        .timer-display {{
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 10px;
                        }}
                        .timer-box {{
                            background: white;
                            border: 2px solid #374151;
                            border-radius: 8px;
                            width: 80px;
                            height: 80px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 2.5rem;
                            font-weight: 700;
                            color: #111827;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                        }}
                        .timer-dots {{
                            display: flex;
                            flex-direction: column;
                            gap: 8px;
                        }}
                        .dot {{
                            width: 6px;
                            height: 6px;
                            background: #374151;
                            border-radius: 50%;
                        }}
                    </style>
                    <script>
                        function startTimer(duration, display) {{
                            var timer = duration, minutes, seconds;
                            var interval = setInterval(function () {{
                                minutes = parseInt(timer / 60, 10);
                                seconds = parseInt(timer % 60, 10);

                                minutes = minutes < 10 ? "0" + minutes : minutes;
                                seconds = seconds < 10 ? "0" + seconds : seconds;

                                document.getElementById('m').textContent = minutes;
                                document.getElementById('s').textContent = seconds;

                                if (--timer < 0) {{
                                    clearInterval(interval);
                                    // Optional: Signal finish?
                                }}
                            }}, 1000);
                        }}

                        window.onload = function () {{
                            var remaining = {int(remaining)};
                            startTimer(remaining);
                        }};
                    </script>
                    </head>
                    <body>
                        <div class="timer-display">
                            <div class="timer-box" id="m">{m:02d}</div>
                            <div class="timer-dots">
                                <div class="dot"></div>
                                <div class="dot"></div>
                            </div>
                            <div class="timer-box" id="s">{s:02d}</div>
                        </div>
                    </body>
                    </html>
                    """
                    components.html(html_code, height=120)

                    # Show ONLY Stop Button
                    if st.button("STOP", use_container_width=True, type="secondary"):
                        st.session_state.timer_running = False
                        st.session_state.expiry_time = None
                        st.rerun()

            else:
                # Editable Inputs (Only show when STOPPED)
                # Use columns to center inputs
                c1, c2, c3 = st.columns([0.45, 0.1, 0.45])
                with c1:
                    st.number_input("Min", min_value=0, max_value=999, label_visibility="collapsed", key="time_left_m")
                with c2:
                    st.markdown("<div class='timer-colon'>:</div>", unsafe_allow_html=True)
                with c3:
                    st.number_input("Sec", min_value=0, max_value=59, label_visibility="collapsed", key="time_left_s")
                
                st.write("") # Spacer
                
                # Start Button
                if st.button("START", use_container_width=True, type="primary"):
                    total_seconds = (st.session_state.time_left_m * 60) + st.session_state.time_left_s
                    if total_seconds > 0:
                        st.session_state.timer_running = True
                        st.session_state.expiry_time = time.time() + total_seconds
                        st.rerun()
                

        # Sources Widget
        with st.container(border=True):
            # Connectivity Check
            is_online = check_internet()
            status_color = "online" if is_online else "offline"
            status_text = "ONLINE" if is_online else "OFFLINE"
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin:0">Sources</h4>
                <span class="status-badge {status_color}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)

            # Tabs
            # Tabs Removed - Unified View
            # tab_offline, tab_online = st.tabs(["Offline Sources", "Online Sources"])
            
            # Helper to fetch sources
            sources_list = []
            try:
                s_resp = requests.get(f"{API_URL}/sources", headers=get_headers())
                if s_resp.status_code == 200:
                    sources_list = s_resp.json()
            except:
                pass

            if sources_list:
                for src in sources_list:
                    # Icon Logic
                    icon = "📄"
                    if src['type'] == 'url': icon = "🌐"
                    elif src['type'] == 'youtube': icon = "📺"
                    
                    c1, c2 = st.columns([0.85, 0.15])
                    with c1:
                        st.markdown(f"""
                        <div class="source-item">
                            <span class="source-icon">{icon}</span>
                            <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{src['filename']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        if st.button("🗑️", key=f"del_{src['id']}", help="Delete source", type="tertiary"):
                            try:
                                # Optimistically update UI by removing from list or just rerun
                                requests.delete(f"{API_URL}/sources/{src['id']}", headers=get_headers())
                                time.sleep(0.1) # Small delay for DB prop
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.markdown("""
                    <div style="text-align: center; color: #9CA3AF; padding: 20px; font-size: 0.9rem;">
                        No sources added
                    </div>
                    """, unsafe_allow_html=True)

            # --- Add Source Section ---
            st.markdown("<br>", unsafe_allow_html=True)
            
            # PDF Upload
            with st.expander("+ Add PDF / Document"):
                uploaded = st.file_uploader("Upload PDF", type=["pdf", "txt"], label_visibility="collapsed")
                if uploaded:
                    # Check duplication in session state to prevent infinite rerun loop
                    if "processed_files" not in st.session_state:
                            st.session_state.processed_files = set()

                    if uploaded.name not in st.session_state.processed_files:
                        try:
                            # Send to backend
                            files = {"file": (uploaded.name, uploaded, uploaded.type)}
                            with st.spinner("Uploading & Indexing..."):
                                resp = requests.post(f"{API_URL}/upload", files=files, headers=get_headers())
                                if resp.status_code == 200:
                                    st.session_state.processed_files.add(uploaded.name)
                                    st.success(f"Successfully uploaded: {uploaded.name}")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    # Parse error for user-friendly message
                                    try:
                                        error_detail = resp.json().get("detail", resp.text)
                                    except Exception:
                                        error_detail = resp.text
                                    
                                    if "OCR" in str(error_detail) or "scan" in str(error_detail).lower():
                                        st.error(f"📸 {error_detail}")
                                    elif "No readable text" in str(error_detail):
                                        st.error("📄 This PDF appears to be scanned/image-only. OCR could not extract text. Please try a clearer scan or a text-based PDF.")
                                    else:
                                        st.error(f"Upload failed: {error_detail}")
                        except Exception as e:
                            st.error(f"Error: {e}")


            # URL Input
            youtube_enabled = st.session_state.get("app_config", {}).get("youtube_enabled", True)

            if youtube_enabled:
                with st.expander("▶️ Add URL / YouTube"):
                    url_input = st.text_input("URL", placeholder="https://youtube.com/... or any webpage", label_visibility="collapsed")
                    if st.button("Process URL", use_container_width=True):
                        if not url_input:
                            st.warning("Please enter a URL")
                        else:
                            import re as re_mod
                            is_youtube = "youtube.com" in url_input or "youtu.be" in url_input
                            
                            if is_youtube:
                                # Extract video ID
                                vid_match = re_mod.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url_input)
                                if not vid_match:
                                    st.error("❌ Invalid YouTube URL format. Supported: youtube.com/watch?v=ID, youtu.be/ID, or youtube.com/shorts/ID")
                                else:
                                    video_id = vid_match.group(1)
                                    with st.spinner("⏳ Fetching transcript via Invidious..."):
                                        try:
                                            resp = requests.post(f"{API_URL}/ingest_youtube", json={"video_id": video_id}, headers=get_headers(), timeout=120)
                                            if resp.status_code == 200:
                                                st.success("✅ YouTube transcript processed successfully!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                error_detail = resp.json().get('detail', resp.text)
                                                if "No captions available" in str(error_detail):
                                                    st.error("❌ No captions found. Try a video with CC enabled.")
                                                elif "Could not reach any transcript" in str(error_detail):
                                                    st.error("⚠️ Transcript service unavailable. Try again later.")
                                                else:
                                                    st.error(f"Failed: {error_detail}")
                                        except requests.Timeout:
                                            st.error("⏱️ Request timed out. Please try again.")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                            else:
                                # Non-YouTube URL: use server-side ingestion
                                with st.spinner("Fetching content..."):
                                    try:
                                        resp = requests.post(f"{API_URL}/ingest_url", json={"url": url_input}, headers=get_headers(), timeout=120)
                                        if resp.status_code == 200:
                                            st.success(f"✅ {resp.json().get('message', 'Content added!')}")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            error_detail = resp.json().get('detail', resp.text)
                                            st.error(f"Failed: {error_detail}")
                                    except requests.Timeout:
                                        st.error("⏱️ Request timed out. Please try again.")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            else:
                with st.expander("▶️ Add YouTube Video  —  Local Only"):
                    st.info(
                        "⚠️ **YouTube is not available in cloud mode.**\n\n"
                        "HuggingFace Spaces blocks outbound network requests.\n\n"
                        "**To use YouTube sources:**\n"
                        "💻 Run FocusFlow locally with Ollama\n\n"
                        "**Right now you can:**\n"
                        "📄 Upload a PDF of your notes\n"
                        "📋 Paste text directly below"
                    )

            # Paste Text Input
            with st.expander("📋 Paste Text / Notes"):
                paste_label = st.text_input(
                    "Source name (optional)",
                    placeholder="e.g. Chapter 3 Notes, Lecture Summary...",
                    key="paste_label_input"
                )

                paste_text = st.text_area(
                    "Paste your text here",
                    placeholder=(
                        "Paste any text here — lecture notes, "
                        "article content, copied webpage text, "
                        "study notes, anything you want to learn from..."
                    ),
                    height=200,
                    key="paste_text_input"
                )

                word_count = len(paste_text.split()) if paste_text else 0
                if paste_text:
                    st.caption(f"📝 {word_count} words")

                col1, col2 = st.columns([2, 1])
                with col1:
                    process_btn = st.button(
                        "➕ Add as Source",
                        key="process_paste_btn",
                        disabled=len(paste_text.strip()) < 50,
                        use_container_width=True
                    )
                with col2:
                    st.caption("Min 50 chars")

                if process_btn and paste_text.strip():
                    source_name = paste_label.strip() if paste_label.strip() \
                        else f"Pasted Text ({word_count} words)"

                    with st.spinner("Processing your text..."):
                        try:
                            # Use API_URL which is the global backend URL configured in app.py
                            response = requests.post(
                                f"{API_URL}/ingest_text",
                                json={
                                    "text": paste_text.strip(),
                                    "source_name": source_name,
                                    "source_type": "paste"
                                },
                                headers=get_headers()
                            )
                            if response.status_code == 200:
                                st.success(f"✅ '{source_name}' added successfully!")
                                # Remove keys from session_state instead of setting to "" due to Streamlit unchangeable key rules when bound to a widget
                                if "paste_text_input" in st.session_state:
                                    del st.session_state["paste_text_input"]
                                if "paste_label_input" in st.session_state:
                                    del st.session_state["paste_label_input"]
                                time.sleep(1)
                                st.rerun()
                            else:
                                error = response.json().get("detail", "Unknown error")
                                st.error(f"❌ Failed to add text: {error}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                if len(paste_text.strip()) > 0 and len(paste_text.strip()) < 50:
                    st.warning("⚠️ Please paste at least 50 characters.")

# --- FOCUS MODE UI ---
if st.session_state.focus_mode:
    # FOCUS: LEFT COLUMN (CHAT)
    with left_col:
        st.markdown("### 💬 Study Assistant")
        
        # Fixed-height chat container to keep messages inside
        messages = st.container(height=600, border=True)
        with messages:
            for msg in st.session_state.chat_history:
                 with st.chat_message(msg["role"]):
                     st.write(msg["content"])
                     
                     # Show sources for assistant messages
                     if msg["role"] == "assistant" and msg.get("sources"):
                         with st.expander("📚 Sources", expanded=False):
                             for idx, s in enumerate(msg["sources"], 1):
                                 if isinstance(s, dict):
                                     filename = s.get("source", "").split("/")[-1]
                                     page = s.get("page", "N/A")
                                     st.caption(f"{idx}. 📄 {filename}, p.{page}")
        
        # Chat input at bottom - messages will appear in container above
        if prompt := st.chat_input(f"Ask about {st.session_state.active_topic}..."):
             st.session_state.chat_history.append({"role": "user", "content": prompt})
             
             # Call AI
             with st.spinner("Thinking..."):
                 try:
                     # Prepare history
                     history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[:-1][-5:]]
                     resp = requests.post(f"{API_URL}/query", json={"question": prompt, "history": history}, headers=get_headers())
                     if resp.status_code == 200:
                         data = resp.json()
                         ans = data.get("answer", "No answer.")
                         srcs = data.get("sources", [])
                         
                         # Include sources if available
                         if srcs:
                             st.session_state.chat_history.append({"role": "assistant", "content": ans, "sources": srcs})
                         else:
                             st.session_state.chat_history.append({"role": "assistant", "content": ans})
                     else:
                         st.session_state.chat_history.append({"role": "assistant", "content": "Error processing request."})
                 except Exception as e:
                     st.session_state.chat_history.append({"role": "assistant", "content": f"Connection Error: {e}"})
             
             st.rerun()

    # FOCUS: RIGHT COLUMN (LESSON CONTENT) - Scrollable Document Viewer
    with mid_col: 
        topic_title = st.session_state.active_topic
        # Handle case where active_topic is dict or string
        if isinstance(topic_title, dict):
             topic_title = topic_title.get('title', 'Unknown Topic')
             
        st.markdown(f"### 📖 {topic_title}")
        st.markdown("---")
        
        # Unique key for this topic's content
        t_id = st.session_state.active_topic['id'] if isinstance(st.session_state.active_topic, dict) else hash(topic_title)
        content_key = f"content_{t_id}"
        
        # 1. Fetch Content if missing
        if content_key not in st.session_state:
            with st.spinner(f"🤖 AI is writing a lesson for '{topic_title}'..."):
                try:
                    resp = requests.post(f"{API_URL}/generate_lesson", json={"topic": topic_title}, headers=get_headers(), timeout=300)
                    
                    if resp.status_code == 200:
                        st.session_state[content_key] = resp.json()["content"]
                    else:
                        st.session_state[content_key] = f"⚠️ Server Error: {resp.text}"
                        
                except Exception as e:
                    st.session_state[content_key] = f"⚠️ Connection Error: {e}"

        # 2. Render Content in Scrollable Container (like a document viewer)
        lesson_container = st.container(height=650, border=True)
        with lesson_container:
            st.markdown(st.session_state[content_key])
        
        # 3. Exit Button (stays fixed below the scrollable content)
        if st.button("⬅ Finish & Return", use_container_width=True):
             st.session_state.focus_mode = False
             st.rerun()



# --- MIDDLE COLUMN: Intelligent Workspace ---
# --- MIDDLE COLUMN: Intelligent Workspace ---
if not st.session_state.focus_mode:
    with mid_col:
        # Header
        h_col1, h_col2 = st.columns([0.8, 0.2])
        with h_col1:
            st.markdown("### Intelligent Workspace")
        with h_col2:
            if st.button("📊 Analytics"):
                show_analytics_dialog()

        # Reading Content / Chat Area
        # Use native container with border to replace "custom-card" and fix "small box" issue
        with st.container(border=True):
            
            # 1. Chat History / Content (Scrollable Container)
            # using height=500 to create a scrolling area like a real chat app
            chat_container = st.container(height=500)
            
            with chat_container:
                if not st.session_state.chat_history:
                    # Welcome Content
                    st.markdown('<div class="article-title">Welcome to FocusFlow</div>', unsafe_allow_html=True)
                    st.markdown("""
                    <div class="article-text">
                        This is your intelligent workspace. <br>
                        Upload a PDF in the sources panel to get started, or ask a question below.
                        <br><br>
                        Your content will appear here...
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Chat Messages
                    # Chat Messages
                    for i, msg in enumerate(st.session_state.chat_history):
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                            
                            # Source Display Logic (MUST BE INSIDE THE LOOP)
                            if msg["role"] == "assistant" and msg.get("sources"):
                                with st.expander("📚 View Sources", expanded=False):
                                    st.caption("Information retrieved from:")
                                    for idx, s in enumerate(msg["sources"], 1):
                                        # Crash Proof Check: Handle string vs dict
                                        if isinstance(s, str):
                                            st.markdown(f"**{idx}.** {s[:100]}...")
                                        else:
                                            # It is a dictionary
                                            src = s.get("source", "Document")
                                            # Extract filename from path
                                            filename = src.split("/")[-1] if "/" in src else src
                                            page_num = s.get("page", "N/A")
                                            
                                            # Display with nice formatting
                                            st.markdown(f"**{idx}.** 📄 `{filename}` • Page {page_num}")

            # 2. Input Area (Pinned to bottom of the visible card by being outside scroll container)
            with st.form(key="chat_form", clear_on_submit=True):
                cols = st.columns([0.85, 0.15])
                with cols[0]:
                    user_input = st.text_input("Ask a question...", placeholder="Ask a question about your documents...", label_visibility="collapsed", key="chat_input_widget")
                with cols[1]:
                    submit_button = st.form_submit_button("Send", use_container_width=True)
                
                if submit_button and user_input:
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    try:
                        with st.spinner("Thinking..."):
                            # Prepare history (exclude sources for cleanliness)
                            history = [
                                {"role": msg["role"], "content": msg["content"]} 
                                for msg in st.session_state.chat_history[:-1][-5:] # Last 5 valid history items before current question
                            ]
                            
                            resp = requests.post(f"{API_URL}/query", json={"question": user_input, "history": history}, headers=get_headers())
                            if resp.status_code == 200:
                                try:
                                    data = resp.json()
                                    ans = data.get("answer", "No answer.")
                                    srcs = data.get("sources", [])
                                    if srcs:
                                        st.session_state.chat_history.append({"role": "assistant", "content": ans, "sources": srcs})
                                    else:
                                        st.session_state.chat_history.append({"role": "assistant", "content": ans})
                                except Exception as e:
                                    st.session_state.chat_history.append({"role": "assistant", "content": f"Error parsing response: {e}\\n\\nRaw text: {resp.text}"})
                            else:
                                 st.session_state.chat_history.append({"role": "assistant", "content": "Error."})
                    except Exception as e:
                         st.session_state.chat_history.append({"role": "assistant", "content": f"Connection Error: {e}"})
                    
                    st.rerun()


# --- RIGHT COLUMN: Scheduler ---
# --- RIGHT COLUMN: Scheduler ---
# --- RIGHT COLUMN: Scheduler ---
if right_col:
    with right_col:
        # --- CALENDAR WIDGET ---
        today = date.today()
        selected_date = st.date_input("📅 Calendar", value=today)

        # --- LOGIC: Show plan for selected date ---
        # If user selects a future date, show its plan inline
        if selected_date != today:
            delta = selected_date - today
            day_offset = delta.days + 1
            
            st.markdown(f"### 📋 Plan for {selected_date}")
            # Filter plan for this hypothetical day
            day_tasks = [t for t in st.session_state.study_plan if t.get("day") == day_offset]
            
            if day_tasks:
                for t in day_tasks:
                    st.markdown(f"- **{t['title']}**")
            else:
                st.info("No plan generated for this specific date yet.")
            
            st.markdown("---")

        # --- B. TALK TO CALENDAR ---
        with st.form("calendar_chat_form", clear_on_submit=True):
            plan_query = st.text_input("Talk to Calendar...", placeholder="e.g., 'Make a 3 day plan'")
            submitted = st.form_submit_button("🚀 Generate Plan")

            if submitted and plan_query:
                with st.spinner("🤖 AI (1B) is thinking..."):
                    try:
                        # Increased timeout to 300s for safety
                        resp = requests.post(f"{API_URL}/generate_plan", json={"request_text": plan_query}, headers=get_headers(), timeout=300)
                        
                        if resp.status_code == 200:
                            plan_data = resp.json()
                            raw_plan = plan_data.get("days", [])
                            
                            # ROBUST SANITIZATION LOOP
                            for index, task in enumerate(raw_plan):
                                # 1. FORCE UNLOCK DAY 1 (The Fix)
                                if index == 0:
                                    task["status"] = "unlocked"
                                    task["locked"] = False
                                else:
                                    # Default logic for others: Trust 'status' or default to 'locked'
                                    # We ignore the 'locked' boolean fallback to be stricter, 
                                    # ensuring only Day 1 is open initially if not specified.
                                    task["status"] = task.get("status", "locked")
                                    
                                # 2. Fix IDs & Keys
                                if "id" not in task: task["id"] = index + 1
                                task["quiz_passed"] = task.get("quiz_passed", False)
                                task["title"] = task.get("topic", f"Topic {task['id']}") # Fallback title
                            
                            st.session_state.study_plan = raw_plan
                            
                            # AUTO-SAVE: Persist the new plan
                            try:
                                num_days = max([t.get("day", 1) for t in raw_plan]) if raw_plan else 0
                                save_resp = requests.post(f"{API_URL}/student/save_plan", json={
                                    "topics": raw_plan,
                                    "num_days": num_days
                                }, headers=get_headers(), timeout=5)
                                
                                if save_resp.status_code == 200:
                                    st.toast(f"💾 Progress saved: {len(raw_plan)} topics", icon="✅")
                                else:
                                    st.warning(f"Could not save progress: {save_resp.text}")
                            except Exception as e:
                                st.warning(f"Could not save progress: {e}")
                            
                            st.success("📅 Plan Created! Check Today's Topics.")
                            st.rerun()
                        else:
                            st.error(f"Failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        # --- TODAY'S TOPICS (FILTERED BY CURRENT STUDY DAY) ---
        current_day = st.session_state.get("current_study_day", 1)
        st.markdown(f"### Today's Topics (Day {current_day})")
        
        # FILTER: Show tasks for current study day
        todays_tasks = [t for t in st.session_state.study_plan if t.get("day") == current_day]

        if not todays_tasks:
            st.caption("No tasks for today. Ask the calendar to make a plan!")
        else:
            # Group tasks by subject if multiple topics per day
            if len(todays_tasks) > 1:
                st.caption(f"📚 {len(todays_tasks)} topics to cover today")


        for i, task in enumerate(todays_tasks):
            # Display subject badge if available
            subject_badge = ""
            if "subject" in task and task["subject"]:
                subject_badge = f"**{task['subject']}** • "
            
            # 1. COMPLETED
            if task["status"] == "completed":
                st.success(f"✅ {subject_badge}{task['title']}")
                # (Flashcards button REMOVED as requested)

            # 2. ACTIVE / UNLOCKED
            elif task["status"] == "unlocked":
                with st.container(border=True):
                    # Show subject badge prominently
                    if "subject" in task and task["subject"]:
                        st.caption(f"📘 {task['subject']}")
                    st.markdown(f"**{task['title']}**")
                    
                    # The Focus Mode Button
                    if st.button(f"🚀 Start Learning", key=f"start_{task['id']}"):
                        st.session_state.focus_mode = True
                        st.session_state.active_topic = task['title']
                        st.rerun()
                    
                    # 1. THE QUIZ BUTTON
                    if st.button(f"📝 Take Quiz (Unlock Next)", key=f"quiz_btn_{task['id']}"):
                        st.session_state[f"show_quiz_{task['id']}"] = True
                        st.rerun()

                    # 2. THE QUIZ (Inline - no dialog to avoid Streamlit error)
                    if st.session_state.get(f"show_quiz_{task['id']}", False):
                        st.markdown("---")
                        st.write("### 🧠 Knowledge Check")
                        
                        # 1. FETCH QUIZ DATA (Dynamic)
                        quiz_key = f"quiz_data_{task['id']}"
                        if quiz_key not in st.session_state:
                            with st.spinner(f"🤖 Generating quiz for '{task['title']}'..."):
                                try:
                                    resp = requests.post(f"{API_URL}/generate_quiz", json={"topic": task['title']}, headers=get_headers(), timeout=120)
                                    if resp.status_code == 200:
                                        st.session_state[quiz_key] = resp.json().get("quiz", [])
                                    else:
                                        st.error("Failed to generate quiz.")
                                except Exception as e:
                                    st.error(f"Connection error: {e}")

                        quiz_data = st.session_state.get(quiz_key, [])
                        if quiz_data:
                            st.caption("Answer the questions below. Next topic unlocks automatically.")
                            
                            score = 0
                            user_answers = {}

                            # 2. RENDER QUESTIONS
                            for i, q in enumerate(quiz_data):
                                st.markdown(f"**Q{i+1}: {q['question']}**")
                                user_answers[i] = st.radio(
                                    "Select one:",
                                    q['options'],
                                    key=f"q_{task['id']}_{i}"
                                )
                            
                            st.markdown("---")
                            
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("🚀 Submit Quiz", key=f"submit_{task['id']}", use_container_width=True):
                                    # GRADING LOGIC
                                    for i, q in enumerate(quiz_data):
                                        if user_answers[i] == q['answer']:
                                            score += 1
                                    
                                    # STORE SCORE FOR ANALYTICS
                                    st.session_state.topic_scores[task['id']] = {
                                        "topic_title": task['title'],
                                        "score": score,
                                        "total": len(quiz_data),
                                        "percentage": (score / len(quiz_data)) * 100
                                    }
                                    
                                    st.info(f"📊 Your Score: {score}/{len(quiz_data)}")
                                    
                                    #  ALWAYS UNLOCK NEXT TOPIC
                                    st.balloons()
                                    
                                    # --- ADAPTIVE LOGIC (Optional based on score) ---
                                    if score == 3:
                                        st.toast("🚀 Perfect Score! Accelerating future plan...", icon="⚡")
                                        for future_task in st.session_state.study_plan:
                                            if future_task["id"] > task["id"]:
                                                if "Advanced" not in future_task["title"]:
                                                    future_task["title"] = f"Advanced: {future_task['title']}"
                                                    future_task["details"] = "Deep dive with complex examples. (AI Adjusted)"
                                    
                                    elif score == 2:
                                        st.toast("⚠️ Good effort! Adding revision steps...", icon="🛡️")
                                        for future_task in st.session_state.study_plan:
                                            if future_task["id"] > task["id"]:
                                                if "Review" not in future_task["title"]:
                                                    future_task["title"] = f"Review & {future_task['title']}"
                                                    future_task["details"] = "Includes recap of previous concepts. (AI Adjusted)"
                                    
                                    st.success(f"✅ Quiz completed! Unlocking next topic...")
                                    time.sleep(1)
                                    
                                    # UNLOCK NEXT TOPIC
                                    task["status"] = "completed"
                                    task["quiz_passed"] = True
                                    
                                    current_id = task["id"]
                                    for next_task in st.session_state.study_plan:
                                        if next_task["id"] == current_id + 1:
                                            next_task["status"] = "unlocked"
                                            next_task["locked"] = False
                                            break
                                    
                                    # AUTO-SAVE: Persist quiz score and completion
                                    try:
                                        subject = task.get("subject", "General")
                                        requests.post(f"{API_URL}/student/quiz_complete", json={
                                            "topic_id": task["id"],
                                            "topic_title": task["title"],
                                            "subject": subject,
                                            "score": score,
                                            "total": len(quiz_data),
                                            "time_taken": 0
                                        }, headers=get_headers(), timeout=5)
                                    except Exception:
                                        pass  # Silent fail for auto-save
                                    
                                    # Close Quiz
                                    st.session_state[f"show_quiz_{task['id']}"] = False
                                    st.rerun()
                            
                            with col2:
                                if st.button("✕ Cancel", key=f"cancel_{task['id']}", use_container_width=True):
                                    st.session_state[f"show_quiz_{task['id']}"] = False
                                    st.rerun()

            # 3. LOCKED
            else:
                with st.container(border=True):
                    st.markdown(f"🔒 <span style='color:gray'>{task['title']}</span>", unsafe_allow_html=True)
