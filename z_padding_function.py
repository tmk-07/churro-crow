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

# ===== Google Sheets (no secrets; same pattern as tester.py) =====
import streamlit as st
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---- Constants
SHEET_ID = "1IHC4Ju76c-ftIYiLEZlrb_n1tEVzbzXrSJYVlb6Qht4"
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "leafy-unity-469117-c2",
    "private_key_id": "41ad9507be2a97ec605d18013ec470b31751831e",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCVUDrQxZwwmB2p
... your full key ...
-----END PRIVATE KEY-----""",
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
def write_score_row(username: str, points: int):
    service = get_sheets_service()
    date_str = datetime.now(timezone.utc).strftime("%m/%d/%y")
    body = {"values": [[username, int(points), date_str]]}
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="Scores!A:C",
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return True, result
    except Exception as e:
        import traceback
        return False, f"{e}\n{traceback.format_exc()}"


def append_score(username: str, points: int):
    """Append one row to Scores!A:C — no time_ms."""
    service = get_sheets_service()
    date_str = datetime.now(timezone.utc).strftime("%m/%d/%y")
    body = {"values": [[username, int(points), date_str]]}
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="Scores!A:C",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True, result
    except Exception as e:
        return False, str(e)


# ===== Question banks =====
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
    elapsed_ms = 0
    # Session state
    for k, v in {
        "score_saved": False, "saved_row_id": None, "quiz_active": False,
        "end_time": None, "score": 0, "current_q": None, "feedback": None,
        "last_rerun": time.time(), "question_counter": 0,
        "last_timer_update": time.time(), "username": "", "start_ms": 0
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

    def start_quiz():
        st.session_state.quiz_active = True
        st.session_state.end_time = datetime.now() + timedelta(seconds=10)
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
    qopt = st.selectbox("Choose a mode", ("Padding Practice","Restriction Practice","Padding (w/ SymDiff)"))
    if qopt == "Padding Practice":
        questions = setquestions
    elif qopt == "Restriction Practice":
        questions = resquestions
    else:
        questions = symquestions

    st.write("You have one minute. For restrictions mode, answer with the eliminated set name. 'z' represents null")

    # Start screen
    if not st.session_state.quiz_active:
        st.session_state.username = st.text_input("Enter your name (for the leaderboard):", value=st.session_state.username)

        c1, c2, c3 = st.columns(3)
        if c1.button("Start Quiz", use_container_width=True, key="start_quiz_col_btn"):
            if not st.session_state.username.strip():
                st.warning("Please enter your name to start.")
            else:
                start_quiz()

        if c2.button("🏆 View Leaderboard", key="view_leaderboard_btn"):
            st.session_state.page = "leaderboard"; st.rerun()

        if c3.button("back to home", key="home_btn"):
            st.session_state.page = "start"; st.rerun()

        st.stop()

    # Timer
    now = datetime.now()
    time_left = max((st.session_state.end_time - now).total_seconds(), 0)

    if time_left > 0:
        timer_placeholder = st.empty()
        timer_text = f"⏱️ Time left: {int(time_left//60):02d}:{int(time_left%60):02d}"
        timer_placeholder.subheader(timer_text)

    # Time up: show submit button that WRITES to sheet
    if time_left <= 0:
        st.session_state.quiz_active = False
        st.balloons()
        st.subheader(f"⏰ Time's up! Final Score: {st.session_state.score}")

        # Simple submit button (no columns while debugging)
        if (not st.session_state.score_saved) and st.button("💾 Submit Score to Leaderboard"):
            with st.spinner("Writing to sheet..."):
                ok, resp = append_score(
                    st.session_state.username or "Player",
                    st.session_state.score
                )

            if ok:
                st.session_state.score_saved = True
                # Show full API response (handy while validating)
                st.success("✅ Score submitted to Google Sheets!")
                try:
                    updated_range = resp.get("updates", {}).get("updatedRange", "")
                except AttributeError:
                    updated_range = ""
                st.json(resp)

                # Extract row number from e.g. 'Scores!A12:C12'
                try:
                    cell = updated_range.split("!")[1].split(":")[-1]
                    row_num = int("".join(ch for ch in cell if ch.isdigit()))
                except Exception:
                    row_num = None
                st.session_state.saved_row_id = row_num

                st.markdown(f"[Open Google Sheet](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")
                st.balloons()
            else:
                st.error("❌ Failed to save score:")
                st.code(str(resp))  # full traceback/error string

        if st.session_state.score_saved:
            row_txt = f" (row #{st.session_state.saved_row_id})" if st.session_state.saved_row_id else ""
            # No elapsed_ms now — you removed the time column
            st.success(f"Saved for **{st.session_state.username or 'Player'}** — {st.session_state.score} pts{row_txt}")

        if st.button("🏆 View Leaderboard"):
            st.session_state.page = "leaderboard"
            st.rerun()

        st.stop()


    # Question UI
    st.subheader(f"Question: {st.session_state.current_q[0]} ?")
    with st.form("answer_form", clear_on_submit=True):
        answer = st.text_input("Your answer:", value="")
        if st.form_submit_button("Submit"):
            check_answer(answer)

    # Feedback
    if st.session_state.feedback:
        msg, kind = st.session_state.feedback
        (st.success if kind=="success" else st.error if kind=="error" else st.warning)(msg)

    # Tick timer while active
    if st.session_state.quiz_active:
        current_time = time.time()
        if current_time - st.session_state.last_timer_update > 0.5:
            st.session_state.last_timer_update = current_time
            st.rerun()

    st.write("The timer is kinda buggy")

    if st.button("back to home", key="back_to_home_btn"):
        st.session_state.page = "start"; st.rerun()
