import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid
import random
import time
from datetime import datetime, timedelta, timezone
import streamlit as st
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

SHEET_ID = "1IHC4Ju76c-ftIYiLEZlrb_n1tEVzbzXrSJYVlb6Qht4"
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "leafy-unity-469117-c2",
    "private_key_id": "41ad9507be2a97ec605d18013ec470b31751831e",
    "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCVUDrQxZwwmB2p\neol+gyCB6Pkqm0XkQwsdYOuUMr+2RFC8bFEf6cB/lzLnNp7UPnG+Yc/Oh4OUEwk2\nIjOaAhLANHj0xfaJU28VNWGU9jZRXGo5z8R1oA3SEWyclWMYeLF89P3TTITbCpud\nlb1m8WhjlVo7R8SSdS2cHk4HYHO0mx6RxrfTtLDIEtLUkFyqITpAWDfXKBhzhjaJ\nUSSRBB8uRsECaOImEUKAtGHz8DaohMQrQbcIXF4+zgOyr969hzQPVvyk47Nux4IA\n3yeVYSyqZhOXpnMKaK3RZBNY+kFG1suhd0xSI1r3cDKvJypnlvTl2A7HjfdLHVRM\nFyejdaInAgMBAAECggEAArH7Dc+zXREx3+BNYRI+4PlynflFjrRDHBmmxvsPiNu8\n1VnjMP9IMUVqbtAGl/A0n2omlSTPFDovvWFqqwoEiqGn2UtFgv8Vjz1ycHztSBSx\n+i8s7a6g8TzNSBpOOp/bHFVTy5+i+k07t+F/FL+g0cNdaJqICtjApQPLBskP7Z+k\nI3mN8KtcCjLHOMY9yOo+rVWNGxqYvE/sCcDc1dFngWUcGCPA8MhubzUKe3jUrEby\nKMKx+n5G85epGymj5hWaphPRIcV+0LblX4jdE560FqDibx747co6gZR1tbBLMsJ0\n0xIgadXnDagzDv4Fdft9w2xozagu0IXApxrNBXersQKBgQDGfRRjINdEpH91rwGb\n5zEvHctewhFtyKWRJOKgZAlHbrfNZEjdZvVwXx9Nt6hUitB6vzU5KMKRAhDm7B/L\nEU5QhchqQ9Yk/wvZ/bTa5nAJ+84riw6MVcyscx2vbmpJtXwrPbnI/jYK/KIb+d/r\nrzvabqa3i7S8zjMrE3/iCct6/wKBgQDAk5KllV6s8ByvsQjlu1t3NYs86r0cur+t\neCU+/0SQmLCan6w6TB7Nqj5eyDkjAyttn8y14UbTG7aviEt3DzlhHh9MI3W71bgs\nycStF7oEUHc3d2gQ9Gm8mEb6EKXZC0LpooGunaaS8TqQ7ptTfl8Nt20EjhVJDOno\nHajF3eWg2QKBgBeo6Tk3vPFNunPIvKRc1pwLLSbKc1FmzXWTs//ybLi7FeXBwn3B\nvBf8/rpA3ivVsCwxhqKdnTOzz1f3ZYLLOU6X49/m3iviywLdHyXIuio2fcjq9nz7\n7T3RKwSyYLEQlRCCdxbiVobQvnIfQvXRGY1cCzttx8mJusezt1a2XC75AoGBAI2r\nwwWHppfJKQFjVu1S8Q342Q8ejbNV+28NZTE8L9/ERJ/r+ZMFrt+Ub7/gwo/sZAWI\nutvO+ACUccgel43mKEs3EsU7jQB7ULu6T7MbMmC8JYgrkuZuOF9jE0wh9TCAJWCl\niYvBNOsDBhfbQW+iFyGLIGtqb2RHWMjHEQNHpAe5AoGBALnO/WYUoh69DuVV6nmL\nhj8RpEWL3gn8f/Je2N5SvQz41E1gsQrDJyfXcVTrsg8RMR2rPECHzanehBXxj6UD\niUQSBkwFKCWn00GbOp2kXMuU5XITQLY6hlUDUfW7z8z8m2IDMgq+9SJID2oQf04R\no/noFJoFcqlyWZ0ee4MJpzvs\n-----END PRIVATE KEY-----\n""",
    "client_email": "streamlit-leaderboard@leafy-unity-469117-c2.iam.gserviceaccount.com",
    "client_id": "115981455553110264285",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-leaderboard%40leafy-unity-469117-c2.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

# ---- Single cached client
@st.cache_resource
def get_sheets_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=creds)

# ---- Single writer (3 columns: Player, Points, Date)
# MODIFIED write_test_row function to include mode
def write_test_row(username: str, points: int, mode: str):
    """Append score to specific mode's sheet"""
    try:
        service = get_sheets_service()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Map mode to sheet name
        sheet_name = {
            "Restriction Practice": "Restriction",
            "Padding Practice": "SetOperations",
            "Padding (w/ SymDiff)": "SymDiff"
        }.get(mode, "SetOperations")  # default to SetOperations
        
        body = {"values": [[username, int(points), date_str]]}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:C",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True, result
    except Exception as e:
        import traceback
        error_msg = f"{e}\n{traceback.format_exc()}"
        st.error(f"Write error: {error_msg}")
        return False, error_msg
    # Map mode to sheet name
resquestions = [
    ("R ⊆ R", 'z'), ("B ⊆ B", 'z'), ("G ⊆ G", 'z'), ("Y ⊆ Y", 'z'),
    ("R ⊆ V", 'z'), ("R ⊆ Z", 'r'), ("B ⊆ V", 'z'), ("B ⊆ Z", 'b'),
    ("Y ⊆ V", 'z'), ("Y ⊆ Z", 'y'), ("G ⊆ V", 'z'), ("G ⊆ Z", 'g'),
    ("B ⊆ B'", 'b'), ("R ⊆ R'", 'r'), ("Y ⊆ Y'", 'y'), ("G ⊆ G'", 'g'),
    ("B' ⊆ B", "b'"), ("R' ⊆ R", "r'"), ("Y' ⊆ Y", "y'"), ("G' ⊆ G", "g'"),
    ("B' = B", "v"), ("R' = R", "v"), ("Y' = Y", "v"), ("G' = G", "v"),
    ("V = Z", "v"), ("V ⊆ Z", "v"), ("Z ⊆ V", "z"),
    ("Z ⊆ B", "z"), ("Z ⊆ R", "z"), ("Z ⊆ Y", "z"), ("Z ⊆ G", "z"),
    ("Z = B", "b"), ("Z = R", "r"), ("Z = G", "g"), ("Z = Y", "y"),
]

symquestions = [
    ("V ∩ B", 'b'), ("V ∩ R", 'r'), ("V ∩ G", 'g'), ("V ∩ Y", 'y'),
    ("V ∪ B", 'v'), ("V ∪ R", 'v'), ("V ∪ G", 'v'), ("V ∪ Y", 'v'),
    ("B ∪ B'", 'v'), ("R' ∪ R", 'v'), ("G ∪ G'", 'v'), ("Y' ∪ Y'", 'v'),
    ("B' ∩ B", 'z'), ("R ∩ R'", 'z'), ("G' ∩ G", 'z'), ("Y ∩ Y'", 'z'),
    ("B - B", 'z'), ("R - R", 'z'), ("G - G", 'z'), ("Y - Y", 'z'),
    ("B - B'", 'v'), ("R - R'", 'v'), ("G - G'", 'v'), ("Y - Y'", 'v'),
    ("B' - B", "v"), ("R' - R", "v"), ("G' - G", "v"), ("Y' - Y", "v"),
    ("V - B", "b'"), ("V - R", "r'"), ("V - G", "g'"), ("V - Y", "y'"),
    ("Z - B", 'b'), ("Z - R", 'r'), ("Z - G", 'g'), ("Z - Y", 'y'),
    ("V - Z", 'v'), ("Z - V", 'v'), ("V ∩ Z", 'z'), ("Z ∪ V", 'v'),
]

setquestions = [
    ("V ∩ B", 'b'), ("V ∩ R", 'r'), ("V ∩ G", 'g'), ("V ∩ Y", 'y'),
    ("V ∪ B", 'v'), ("V ∪ R", 'v'), ("V ∪ G", 'v'), ("V ∪ Y", 'v'),
    ("B ∪ B'", 'v'), ("R' ∪ R", 'v'), ("G ∪ G'", 'v'), ("Y ∪ Y'", 'v'),
    ("B' ∩ B", 'z'), ("R ∩ R'", 'z'), ("G' ∩ G", 'z'), ("Y ∩ Y'", 'z'),
    ("B - B", 'z'), ("R - R", 'z'), ("G - G", 'z'), ("Y - Y", 'z'),
    ("B - B'", 'b'), ("R - R'", 'r'), ("G - G'", 'g'), ("Y - Y'", 'y'),
    ("B' - B", "b'"), ("R' - R", "r'"), ("G' - G", "g'"), ("Y' - Y", "y'"),
    ("V - B", "b'"), ("V - R", "r'"), ("V - G", "g'"), ("V - Y", "y'"),
    ("Z - B", 'z'), ("Z - R", 'z'), ("Z - G", 'z'), ("Z - Y", 'z'),
    ("V - Z", 'v'), ("Z - V", 'z'), ("V ∩ Z", 'z'), ("Z ∪ V", 'v'),
]


def padding_practice():
    now = datetime.now()
    # Session state initialization
    for k, v in {
        "score_saved": False, "saved_row_id": None, "quiz_active": False,
        "end_time": None, "score": 0, "current_q": None, "feedback": None,
        "last_rerun": time.time(), "question_counter": 0,
        "last_timer_update": time.time(), "username": "", "start_ms": 0,
        "quiz_mode": "Padding Practice"  # ADDED DEFAULT MODE
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Moved mode selection outside of if-block
    if not st.session_state.quiz_active:
        st.session_state.quiz_mode = st.selectbox(
            "Choose a mode", 
            ("Padding Practice", "Restriction Practice", "Padding (w/ SymDiff)")
        )
    
    # Set questions based on selected mode
    if st.session_state.quiz_mode == "Padding Practice":
        questions = setquestions
    elif st.session_state.quiz_mode == "Restriction Practice":
        questions = resquestions
    else:
        questions = symquestions

    def start_quiz():
        st.session_state.quiz_active = True
        st.session_state.show_results = False
        st.session_state.end_time = datetime.now() + timedelta(seconds=60)  # FIXED: 60 seconds = 1 minute
        st.session_state.start_ms = int(time.time() * 1000)
        st.session_state.score = 0
        st.session_state.current_q = random.choice(questions)
        st.session_state.feedback = None
        st.session_state.question_counter = 0
        st.session_state.last_rerun = time.time()
        st.session_state.last_timer_update = time.time()
        st.session_state.score_saved = False
        st.session_state.saved_row_id = None

    def check_answer(user_answer):
        if not user_answer.strip():
            st.session_state.feedback = ("Please enter an answer", "warning")
            return
        user_answer_lower = user_answer.strip().lower()
        if user_answer_lower == st.session_state.current_q[1]:
            st.session_state.score += 1
            st.session_state.feedback = ("Correct!", "success")
            st.session_state.current_q = random.choice(questions)
            st.session_state.question_counter += 1
        else:
            st.session_state.feedback = ("Wrong.", "error")

    # UI
    st.title("OS Quick Padding Practice - leaderboard work in progress")
    # REMOVED DUPLICATE MODE SELECTBOX HERE

    st.write("You have one minute. For restrictions mode, answer with the eliminated set name. 'z' represents null")

    # Start screen - show when quiz is not active
    if not st.session_state.quiz_active:
        st.session_state.username = st.text_input("Enter name (opt):", value=st.session_state.username)
 
        c1, c2, c3 = st.columns(3)
        if c1.button("Start Quiz", use_container_width=True, key="start_quiz_col_btn"):
            start_quiz()
            st.rerun()

        if c2.button("🏆 View Leaderboard", key="view_leaderboard_btn"):
            st.session_state.page = "leaderboard"; st.rerun()

        if c3.button("back to home", key="home_btn"):
            st.session_state.page = "start"; st.rerun()

    # Quiz screen - show when quiz is active
    else:
        # Calculate time remaining
        now = datetime.now()
        if st.session_state.end_time:
            time_left = max((st.session_state.end_time - now).total_seconds(), 0)
        else:
            time_left = 0

        # Timer display
        if time_left > 0:
            timer_text = f"⏱️ Time left: {int(time_left//60):02d}:{int(time_left%60):02d}"
            st.subheader(timer_text)

        # Time up: show results and submit button
        if time_left <= 0:
            st.subheader(f"Your score: {st.session_state.score} points")
            
            # Submit to leaderboard
            if not st.session_state.score_saved:
                if st.button("💾 Submit Score to Leaderboard"):
                    with st.spinner("Writing to sheet..."):
                        # FIXED: Added mode parameter
                        ok, resp = write_test_row(
                            st.session_state.username or "Player",
                            st.session_state.score,
                            st.session_state.quiz_mode  # ADDED MODE
                        )
                    if ok:
                        st.session_state.score_saved = True
                        st.success("✅ Score submitted to leaderboard!")
                    else:
                        st.error("❌ Failed to save score:")
                        st.code(str(resp))

            # Play again or view leaderboard
            col1, col2 = st.columns(2)
            if col1.button("Play Again"):
                start_quiz()
                st.rerun()
            if col2.button("🏆 View Leaderboard"):
                st.session_state.page = "leaderboard"
                st.rerun()

        # Quiz still active - show question UI
        else:
            st.subheader(f"Question: {st.session_state.current_q[0]} ?")
            with st.form("answer_form", clear_on_submit=True):
                answer = st.text_input("Your answer:", value="")
                if st.form_submit_button("Submit"):
                    check_answer(answer)

            # Feedback
            if st.session_state.feedback:
                msg, kind = st.session_state.feedback
                if kind == "success":
                    st.success(msg)
                elif kind == "error":
                    st.error(msg)
                else:
                    st.warning(msg)

            # Tick timer while active
            current_time = time.time()
            if current_time - st.session_state.last_timer_update > 0.5:
                st.session_state.last_timer_update = current_time
                st.rerun()

    # Back to home button (show in both states)
    if st.button("back to home", key="back_to_home_btn"):
        st.session_state.page = "start"
        st.rerun()