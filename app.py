import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import streamlit.components.v1 as components
from streamlit_calendar import calendar
from datetime import date

# -----------------------------------------------------------------------------
# 1. CONFIG & CSS
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FocusFlow")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Reset & Fonts */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F2937;
        background-color: #FAFAFA;
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
</style>
""", unsafe_allow_html=True)

# Backend URL
API_URL = "http://localhost:8000"

# Session State
if "timer_running" not in st.session_state: st.session_state.timer_running = False
if "expiry_time" not in st.session_state: st.session_state.expiry_time = None
if "time_left_m" not in st.session_state: st.session_state.time_left_m = 0
if "time_left_s" not in st.session_state: st.session_state.time_left_s = 0
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "mastery_data" not in st.session_state: st.session_state.mastery_data = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
if "expanded_topics" not in st.session_state: st.session_state.expanded_topics = set()
if "show_analytics" not in st.session_state: st.session_state.show_analytics = False

# Focus Mode State
if "focus_mode" not in st.session_state: st.session_state.focus_mode = False
if "active_topic" not in st.session_state: st.session_state.active_topic = None
if "study_plan" not in st.session_state:
    # START EMPTY as requested
    st.session_state.study_plan = [] 

# ... (check_internet remains)

# ... (Search logic remains)

# ...



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

@st.dialog("Analytics Overview", width="large")
def show_analytics_dialog():
    # Header Tabs
    st.markdown("""
    <div style="display: flex; gap: 10px; margin-bottom: 30px; background: #F3F4F6; padding: 5px; border-radius: 8px;">
        <button style="flex: 1; padding: 8px; border-radius: 6px; border: none; background: #3B82F6; color: white; font-weight: 600;">S1</button>
        <button style="flex: 1; padding: 8px; border-radius: 6px; border: none; background: transparent; color: #6B7280; font-weight: 600;">S2</button>
        <button style="flex: 1; padding: 8px; border-radius: 6px; border: none; background: transparent; color: #6B7280; font-weight: 600;">S3</button>
        <button style="flex: 1; padding: 8px; border-radius: 6px; border: none; background: transparent; color: #6B7280; font-weight: 600;">S4</button>
    </div>
    """, unsafe_allow_html=True)
    
    # Hero Score
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 5rem; color: #111827; margin: 0;">67%</h1>
        <p style="color: #6B7280; font-size: 1.2rem;">Overall Mastery</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Columns
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**G** <span style='float:right; background:#d1d5db; color:white; padding:2px 8px; border-radius:99px; font-size:0.8rem'>N/A</span>", unsafe_allow_html=True)
        st.markdown("<p style='color:#4B5563; margin-top:10px'>--</p>", unsafe_allow_html=True)

    with c2:
        st.markdown("**M** <span style='float:right; background:#d1d5db; color:white; padding:2px 8px; border-radius:99px; font-size:0.8rem'>N/A</span>", unsafe_allow_html=True)
        st.markdown("<p style='color:#4B5563; margin-top:10px'>--</p>", unsafe_allow_html=True)

    with c3:
        st.markdown("**P** <span style='float:right; background:#d1d5db; color:white; padding:2px 8px; border-radius:99px; font-size:0.8rem'>N/A</span>", unsafe_allow_html=True)
        st.markdown("<p style='color:#4B5563; margin-top:10px'>--</p>", unsafe_allow_html=True)

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
                resp = requests.post(f"{API_URL}/unlock_topic", json=payload)
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
                s_resp = requests.get(f"{API_URL}/sources")
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
                                requests.delete(f"{API_URL}/sources/{src['id']}")
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
                                resp = requests.post(f"{API_URL}/upload", files=files)
                                if resp.status_code == 200:
                                    st.session_state.processed_files.add(uploaded.name)
                                    st.success(f"Successfully uploaded: {uploaded.name}")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Upload failed: {resp.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

            # URL Input
            with st.expander("+ Add URL / YouTube"):
                url_input = st.text_input("URL", placeholder="https://youtube.com/...", label_visibility="collapsed")
                if st.button("Process URL", use_container_width=True):
                    if not url_input:
                        st.warning("Please enter a URL")
                    else:
                        with st.spinner("Fetching & Indexing..."):
                            try:
                                resp = requests.post(f"{API_URL}/ingest_url", json={"url": url_input})
                                if resp.status_code == 200:
                                    data = resp.json()
                                    st.success(data["message"])
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {resp.text}")
                            except Exception as e:
                                st.error(f"Error: {e}")

# --- FOCUS MODE UI ---
if st.session_state.focus_mode:
    # FOCUS: LEFT COLUMN (CHAT)
    with left_col:
        st.markdown("### 💬 Study Assistant")
        # Reuse existing chat logic or a simplified version
        messages = st.container(height=600)
        with messages:
            for msg in st.session_state.chat_history:
                 with st.chat_message(msg["role"]):
                     st.write(msg["content"])
        
        # New Chat Input
        if prompt := st.chat_input(f"Ask about {st.session_state.active_topic}..."):
             st.session_state.chat_history.append({"role": "user", "content": prompt})
             with st.chat_message("user"):
                 st.write(prompt)
             
             # Call AI
             with st.chat_message("assistant"):
                 with st.spinner("Thinking..."):
                     try:
                         # Prepare history
                         history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[:-1][-5:]]
                         resp = requests.post(f"{API_URL}/query", json={"question": prompt, "history": history})
                         if resp.status_code == 200:
                             data = resp.json()
                             ans = data.get("answer", "No answer.")
                             st.write(ans)
                             st.session_state.chat_history.append({"role": "assistant", "content": ans})
                         else:
                             st.error("Error.")
                     except Exception as e:
                         st.error(f"Connection Error: {e}")

    # FOCUS: RIGHT COLUMN (CONTENT) - (Technically mid_col in layout)
    with mid_col: 
        st.markdown(f"## 📖 {st.session_state.active_topic}")
        st.info("Here is the learning material for this topic.")
        
        # Placeholder Content
        st.markdown("""
        ### Key Concepts
        - **Concept 1:** Definition and importance.
        - **Concept 2:** Real-world application.
        - **Concept 3:** Detailed analysis.
        """)
        
        # Exit Button
        st.markdown("---")
        if st.button("⬅️ Exit Focus Mode", use_container_width=True):
             st.session_state.focus_mode = False
             st.session_state.active_topic = None
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
                                with st.expander("Sources used"):
                                    for s in msg["sources"]:
                                        # Crash Proof Check: Handle string vs dict
                                        if isinstance(s, str):
                                            st.info(f"📄 {s[:100]}...")
                                        else:
                                            # It is a dictionary
                                            src = s.get("source", "Document")
                                            page_num = s.get("page", 1)
                                            label = f"📄 {src} | Page {page_num}"
                                            st.caption(label)
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
                            
                            resp = requests.post(f"{API_URL}/query", json={"question": user_input, "history": history})
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
        # Scheduler Header Removed to save space
        # st.markdown("### Scheduler")
        
        # Calendar Agent
        # Calendar Agent (Minimalist)
        # Removing st.container() wrapper to reduce vertical gap/white block
        
        # Calculate Start Date: 1st of Previous Month
        today = date.today()
        # Logic to go back 1 month
        last_month_year = today.year if today.month > 1 else today.year - 1
        last_month = today.month - 1 if today.month > 1 else 12
        start_date_str = f"{last_month_year}-{last_month:02d}-01"

        calendar_options = {
            # User requested arrows "on both sides"
            "headerToolbar": {"left": "prev", "center": "title", "right": "next"},
            
            "initialView": "multiMonthYear",
            "initialDate": start_date_str, 
            "views": {
                "multiMonthYear": {
                    "type": "multiMonthYear",
                    "duration": {"months": 3},
                    "multiMonthMaxColumns": 3,
                    # FIXED: 280px ensures text is readable. 100px was too small!
                    # This will force the container to scroll horizontally.
                    "multiMonthMinWidth": 280, 
                }
            },
            # JS Option to format title shorter (e.g. "Dec 2025 - Feb 2026")
            "titleFormat": {"year": "numeric", "month": "short"}, 
            # "contentHeight": "auto",
        }
        
        calendar(events=[], options=calendar_options, key="mini_cal")
        
        # --- B. TALK TO CALENDAR (Fixed: No Loop) ---
        with st.form("calendar_chat_form", clear_on_submit=True):
            plan_query = st.text_input("Talk to Calendar...", placeholder="e.g., 'Make a 3 day plan'")
            submitted = st.form_submit_button("🚀 Generate Plan")

            if submitted and plan_query:
                with st.spinner("🤖 AI (1B) is thinking..."):
                    try:
                        # Increased timeout to 300s for safety
                        resp = requests.post(f"{API_URL}/generate_plan", json={"request_text": plan_query}, timeout=300)
                        
                        if resp.status_code == 200:
                            plan_data = resp.json()
                            raw_plan = plan_data.get("days", [])
                            
                            # ROBUST SANITIZATION LOOP
                            for index, task in enumerate(raw_plan):
                                # 1. Fix Missing ID (Use index + 1 if missing)
                                if "id" not in task:
                                    task["id"] = index + 1
                                
                                # 2. Fix Missing Keys
                                task["quiz_passed"] = task.get("quiz_passed", False)
                                task["status"] = task.get("status", "locked" if task.get("locked", True) else "unlocked")
                                task["title"] = task.get("topic", f"Topic {task['id']}") # Fallback title
                            
                            st.session_state.study_plan = raw_plan
                            st.success("📅 Plan Created! Check Today's Topics.")
                            st.rerun()
                        else:
                            st.error(f"Failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        # NO SPACER here

        # Removed spacer to satisfy "remove white box" request
        # st.markdown("<br>", unsafe_allow_html=True) # Spacer

        # Today's Topics (Gamified)
        # Merging the opening DIV and the Header into ONE markdown call to ensure they render together.
        st.markdown("""
            <div class="custom-card">
            <div style="display:flex; justify-content:space-between; align-items:center;"><h4>Today's Topics</h4></div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.study_plan:
            # EMPTY STATE
            st.info("Tell the calendar to make a plan 📅")
        else:
            # Render Plan
            st.markdown(f'<span style="font-size:0.8rem; color:#6B7280">{len([t for t in st.session_state.study_plan if t["quiz_passed"]])}/{len(st.session_state.study_plan)} Done</span>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Iterate through Mock Plan
            for i, topic in enumerate(st.session_state.study_plan):
                t_id = topic["id"]
                title = topic["title"]
                status = topic["status"]
                passed = topic["quiz_passed"]
                
                # Styles
                opacity = "1.0" if status == "unlocked" else "0.5"
                icon = "🔒" if status == "locked" else ("✅" if passed else "🟦")
                
                # Card Container
                with st.container():
                    c1, c2 = st.columns([0.15, 0.85])
                    with c1:
                        st.markdown(f"<div style='font-size:1.5rem; opacity:{opacity}'>{icon}</div>", unsafe_allow_html=True)
                    with c2:
                        # Title
                        st.markdown(f"<div style='font-weight:600; opacity:{opacity}'>{title}</div>", unsafe_allow_html=True)
                        
                        # Unlocked & Not Passed -> Show Actions
                        if status == "unlocked" and not passed:
                            # Dropdown / Expandable Area
                            with st.expander("Start Learning", expanded=True):
                                # FOCUS MODE TRIGGER
                                if st.button("🚀 Enter Focus Mode", key=f"focus_{t_id}", use_container_width=True):
                                    st.session_state.focus_mode = True
                                    st.session_state.active_topic = title
                                    st.rerun()

                                st.info("Mastery Required: 80%")
                                if st.button("Take Mandatory Quiz", key=f"q_{t_id}", type="primary", use_container_width=True):
                                    show_quiz_dialog(t_id, title)
                                
                                if st.button("Flashcards (Optional)", key=f"fc_{t_id}", use_container_width=True):
                                    show_flashcard_dialog(t_id, title)
                
                st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
                
        st.markdown("</div>", unsafe_allow_html=True)
