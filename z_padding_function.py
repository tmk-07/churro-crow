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
import threading

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
    # ... existing code ...

    # Start screen - show when quiz is not active
    if not st.session_state.quiz_active:
        st.session_state.username = st.text_input("Enter name (opt):", value=st.session_state.username, autocomplete="off")
 
        c1, c2, c3 = st.columns(3)
        if c1.button("Start Quiz", use_container_width=True, key="start_quiz_col_btn"):
            start_quiz()
            st.rerun()

        if c2.button("🏆 View Leaderboard", key="view_leaderboard_btn"):
            st.session_state.page = "leaderboard"
            st.rerun()

        if c3.button("back to home", key="home_btn_main"):
            st.session_state.page = "start"
            st.rerun()

    # Quiz screen - show when quiz is active
    else:
        # ... existing timer and question code ...

        # Time up: show results and submit button
        if time_left <= 0:
            st.subheader(f"Your score: {st.session_state.score} points")
            
            # Submit to leaderboard
            if not st.session_state.score_saved:
                if st.button("💾 Submit Score to Leaderboard", key="submit_score_btn"):
                    with st.spinner("Writing to sheet..."):
                        ok, resp = write_test_row(
                            st.session_state.username or "Player",
                            st.session_state.score,
                            st.session_state.quiz_mode
                        )
                    if ok:
                        st.session_state.score_saved = True
                        st.success("✅ Score submitted to leaderboard!")
                    else:
                        st.error("❌ Failed to save score:")
                        st.code(str(resp))

            # Play again or view leaderboard
            col1, col2 = st.columns(2)
            if col1.button("Play Again", key="play_again_btn"):
                start_quiz()
                st.rerun()
            if col2.button("🏆 View Leaderboard", key="view_leaderboard_quiz_btn"):
                st.session_state.page = "leaderboard"
                st.rerun()

        # Quiz still active - show question UI
        else:
            st.subheader(f"Question: {st.session_state.current_q[0]} ?")
            with st.form("answer_form", clear_on_submit=True):
                answer = st.text_input("Your answer:", value="", autocomplete="off", key="answer_input")
                if st.form_submit_button("Submit", key="submit_answer_btn"):
                    check_answer(answer)

            # ... existing feedback code ...

    # Back to home button (show in both states)
    if st.button("back to home", key="back_to_home_btn_unique"):
        st.session_state.page = "start"
        st.rerun()
