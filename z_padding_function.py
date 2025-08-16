import os
import time
import uuid
import random
import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone

import streamlit as st
from PIL import Image
from google.oauth2 import service_account
from googleapiclient.discovery import build

# If you need these elsewhere in your app, keep the import.
from churrooscalc import (
    double_set, set_cards, parseR, quick_solutions, calc_full_solution,
    validate_inputs, cards, universeRefresher, gen_full_solution
)

# ==============================
# Google Sheets config
# ==============================
SHEET_ID = "1IHC4Ju76c-ftIYiLEZlrb_n1tEVzbzXrSJYVlb6Qht4"
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "leafy-unity-469117-c2",
    "private_key_id": "41ad9507be2a97ec605d18013ec470b31751831e",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCVUDrQxZwwmB2p
eol+gyCB6Pkqm0XkQwsdYOuUMr+2RFC8bFEf6cB/lzLnNp7UPnG+Yc/Oh4OUEwk2
IjOaAhLANHj0xfaJU28VNWGU9jZRXGo5z8R1oA3SEWyclWMYeLF89P3TTITbCpud
lb1m8WhjlVo7R8SSdS2cHk4HYHO0mx6RxrfTtLDIEtLUkFyqITpAWDfXKBhzhjaJ
USSRBB8uRsECaOImEUKAtGHz8DaohMQrQbcIXF4+zgOyr969hzQPVvyk47Nux4IA
3yeVYSyqZhOXpnMKaK3RZBNY+kFG1suhd0xSI1r3cDKvJypnlvTl2A7HjfdLHVRM
FyejdaInAgMBAAECggEAArH7Dc+zXREx3+BNYRI+4PlynflFjrRDHBmmxvsPiNu8
1VnjMP9IMUVqbtAGl/A0n2omlSTPFDovvWFqqwoEiqGn2UtFgv8Vjz1ycHztSBSx
+i8s7a6g8TzNSBpOOp/bHFVTy5+i+k07t+F/FL+g0cNdaJqICtjApQPLBskP7Z+k
I3mN8KtcCjLHOMY9yOo+rVWNGxqYvE/sCcDc1dFngWUcGCPA8MhubzUKe3jUrEby
KMKx+n5G85epGymj5hWaphPRIcV+0LblX4jdE560FqDibx747co6gZR1tbBLMsJ0
0xIgadXnDagzDv4Fdft9w2xozagu0IXApxrNBXersQKBgQDGfRRjINdEpH91rwGb
5zEvHctewhFtyKWRJOKgZAlHbrfNZEjdZvVwXx9Nt6hUitB6vzU5KMKRAhDm7B/L
EU5QhchqQ9Yk/wvZ/bTa5nAJ+84riw6MVcyscx2vbmpJtXwrPbnI/jYK/KIb+d/r
rzvabqa3i7S8zjMrE3/iCct6/wKBgQDAk5KllV6s8ByvsQjlu1t3NYs86r0cur+t
eCU+/0SQmLCan6w6TB7Nqj5eyDkjAyttn8y14UbTG7aviEt3DzlhHh9MI3W71bgs
ycStF7oEUHc3d2gQ9Gm8mEb6EKXZC0LpooGunaaS8TqQ7ptTfl8Nt20EjhVJDOno
HajF3eWg2QKBgBeo6Tk3vPFNunPIvKRc1pwLLSbKc1FmzXWTs//ybLi7FeXBwn3B
vBf8/rpA3ivVsCwxhqKdnTOzz1f3ZYLLOU6X49/m3iviywLdHyXIuio2fcjq9nz7
7T3RKwSyYLEQlRCCdxbiVobQvnIfQvXRGY1cCzttx8mJusezt1a2XC75AoGBAI2r
wwWHppfJKQFjVu1S8Q342Q8ejbNV+28NZTE8L9/ERJ/r+ZMFrt+Ub7/gwo/sZAWI
utvO+ACUccgel43mKEs3EsU7jQB7ULu6T7MbMmC8JYgrkuZuOF9jE0wh9TCAJWCl
iYvBNOsDBhfbQW+iFyGLIGtqb2RHWMjHEQNHpAe5AoGBALnO/WYUoh69DuVV6nmL
hj8RpEWL3gn8f/Je2N5SvQz41E1gsQrDJyfXcVTrsg8RMR2rPECHzanehBXxj6UD
iUQSBkwFKCWn00GbOp2kXMuU5XITQLY6hlUDUfW7z8z8m2IDMgq+9SJID2oQf04R
o/noFJoFcqlyWZ0ee4MJpzvs
-----END PRIVATE KEY-----""",
    "client_email": "streamlit-leaderboard@leafy-unity-469117-c2.iam.gserviceaccount.com",
    "client_id": "115981455553110264285",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-leaderboard%40leafy-unity-469117-c2.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

@st.cache_resource
def get_sheets_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=creds)

def write_test_row(username: str, points: int, mode: str):
    """Append score to the appropriate sheet tab."""
    try:
        service = get_sheets_service()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sheet_name = {
            "Restriction Practice": "Restriction",
            "Padding Practice": "SetOperations",
            "Padding (w/ SymDiff)": "SymDiff",
        }.get(mode, "SetOperations")
        body = {"values": [[username, int(points), date_str]]}
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:C",
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return True, result
    except Exception as e:
        import traceback
        return False, f"{e}\n{traceback.format_exc()}"

# ==============================
# Question banks
# ==============================
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

# ==============================
# The page/app function
# ==============================
def padding_practice():
    """Self-contained quiz with namespaced session_state keys (pp_*)."""

    ss = st.session_state

    # ---------- Initialize namespaced state once ----------
    defaults = {
        "pp_active": False,          # in-quiz?
        "pp_results": False,         # show results?
        "pp_mode": "Padding Practice",
        "pp_username": "",
        "pp_score": 0,
        "pp_q": None,
        "pp_feedback": None,
        "pp_qseq": 0,               # increments each question for unique form keys
        "pp_runid": "",             # unique per run to isolate keys
        "pp_end_ts": 0.0,           # UNIX seconds when quiz ends
        "pp_tick": 0.0,             # throttles reruns for timer (~2x/sec)
        "pp_saved": False,          # saved to Sheets?
    }
    for k, v in defaults.items():
        if k not in ss:
            ss[k] = v

    # ---------- Mode select (only when not in quiz/results) ----------
    if not ss.pp_active and not ss.pp_results:
        ss.pp_mode = st.selectbox(
            "Choose a mode",
            ("Padding Practice", "Restriction Practice", "Padding (w/ SymDiff)"),
            key="pp_mode_select",
        )

    # ---------- Question pool ----------
    if ss.pp_mode == "Padding Practice":
        questions = setquestions
    elif ss.pp_mode == "Restriction Practice":
        questions = resquestions
    else:
        questions = symquestions

    # ---------- Helpers ----------
    def start_quiz():
        ss.pp_active = True
        ss.pp_results = False
        ss.pp_end_ts = time.time() + 60      # ← change to +10 while testing
        ss.pp_runid = uuid.uuid4().hex
        ss.pp_qseq = 0
        ss.pp_score = 0
        ss.pp_q = random.choice(questions)
        ss.pp_feedback = None
        ss.pp_saved = False

    def check_answer(user_answer: str):
        ans = (user_answer or "").strip().lower()
        if not ans:
            ss.pp_feedback = ("Please enter an answer", "warning")
            return
        if ans == ss.pp_q[1]:
            ss.pp_score += 1
            ss.pp_feedback = ("Correct!", "success")
        else:
            ss.pp_feedback = ("Wrong.", "error")
        ss.pp_q = random.choice(questions)
        ss.pp_qseq += 1

    # ---------- Header ----------
    st.title("OS Quick Padding Practice")
    st.write("You have one minute. For restrictions mode, answer with the eliminated set name. 'z' represents null")

    # =========================
    # RESULTS SCREEN
    # =========================
    if ss.pp_results:
        st.subheader(f"Your score: {ss.pp_score} points")

        if not ss.pp_saved:
            if st.button("💾 Submit Score to Leaderboard", key="pp_submit_score"):
                with st.spinner("Writing to sheet..."):
                    ok, resp = write_test_row(
                        ss.pp_username or "Player",
                        ss.pp_score,
                        ss.pp_mode,
                    )
                if ok:
                    ss.pp_saved = True
                    st.success("✅ Score submitted to leaderboard!")
                else:
                    st.error("❌ Failed to save score:")
                    st.code(str(resp))

        col1, col2 = st.columns(2)
        if col1.button("Play Again", key="pp_play_again"):
            start_quiz()
            st.rerun()
        if col2.button("🏆 View Leaderboard", key="pp_view_leaderboard_results"):
            ss.page = "leaderboard"
            st.rerun()

        if st.button("Back to Home", key="pp_home_results"):
            ss.page = "start"
            st.rerun()
        return  # stop here

    # =========================
    # START SCREEN
    # =========================
    if not ss.pp_active:
        ss.pp_username = st.text_input(
            "Enter name (opt):",
            value=ss.pp_username,
            autocomplete="off",
            key="pp_name_input",
        )
        c1, c2, c3 = st.columns(3)
        if c1.button("Start Quiz", use_container_width=True, key="pp_start"):
            start_quiz()
            st.rerun()
        if c2.button("🏆 View Leaderboard", key="pp_view_leaderboard_start"):
            ss.page = "leaderboard"
            st.rerun()
        if c3.button("Back to Home", key="pp_home_start"):
            ss.page = "start"
            st.rerun()
        return  # stop here

    # =========================
    # QUIZ SCREEN
    # =========================
    # Timer
    end_ts = ss.pp_end_ts or 0
    time_left = max(int(end_ts - time.time()), 0)

    timer_ph = st.empty()
    timer_ph.subheader(f"⏱️ Time left: {time_left//60:02d}:{time_left%60:02d}")

    if time_left == 0:
        ss.pp_active = False
        ss.pp_results = True
        st.rerun()

    # Question UI
    st.subheader(f"Question: {ss.pp_q[0]} ?")
    run_id = ss.pp_runid
    q_seq = ss.pp_qseq
    form_key = f"pp_form_{run_id}_{q_seq}"

        # Use a stable key that does NOT change per question/run
    ANSWER_KEY = "answer_value"

    answer = st.text_input("Your answer:", key=ANSWER_KEY, autocomplete="off")
    if st.button("Submit answer"):
        if answer.strip():
            check_answer(answer)
            st.session_state[ANSWER_KEY] = ""  # clear for next entry


    # Feedback
    if ss.pp_feedback:
        msg, kind = ss.pp_feedback
        if kind == "success":
            st.success(msg)
        elif kind == "error":
            st.error(msg)
        else:
            st.warning(msg)


    # Bottom navigation
    if st.button("Back to Home", key="pp_home_bottom"):
        ss.page = "start"
        st.rerun()
