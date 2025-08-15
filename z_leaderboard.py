# z_leaderboard.py
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timezone
import time

# Initialize Google Sheets API
def get_sheet_service():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=creds)

def get_leaderboard(limit=20):
    try:
        service = get_sheet_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=st.secrets["gcp_service_account"]["SHEET_ID"],
            range="Scores!A:D"  # Columns: Name, Points, Time(ms), Timestamp
        ).execute()
        values = result.get('values', [])
        return values[1:] if len(values) > 1 else []  # Skip header row
    except Exception as e:
        st.error(f"Error loading leaderboard: {str(e)}")
        return []

def add_score(username: str, points: int, time_ms: int):
    try:
        service = get_sheet_service()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        values = [[username, points, time_ms, timestamp]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=st.secrets["gcp_service_account"]["SHEET_ID"],
            range="Scores",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save score: {str(e)}")
        return False

def leaderboard_page():
    if st.button("Initialize Sheet (First Time Only)",key="init_sheet_btn"):
        init_sheet()
    st.title("🏆 Leaderboard 0")

    # Display leaderboard
    scores = get_leaderboard()
    if scores:
        # Convert to DataFrame
        df = pd.DataFrame(scores, columns=["Player", "Points", "Time (ms)", "When (UTC)"])
        df["Points"] = df["Points"].astype(int)
        df["Time (s)"] = (df["Time (ms)"].astype(int) / 1000).round(2)
        
        # Sort: Higher points first, then faster times
        df = df.sort_values(by=["Points", "Time (ms)"], ascending=[False, True])
        
        st.dataframe(df[["Player", "Points", "Time (s)", "When (UTC)"]], hide_index=True)
    else:
        st.info("No scores yet - be the first!")

    # Navigation buttons
    c1, c2 = st.columns(2)
    if c1.button("⬅ Back to Home",key="home_btn"):
        st.session_state.page = "start"
        st.rerun()
    if c2.button("🔁 Refresh Leaderboard"):
        st.rerun()

# Update the init_sheet function
def init_sheet():
    service = get_sheet_service()
    service.spreadsheets().values().update(
        spreadsheetId=st.secrets["gcp_service_account"]["SHEET_ID"],
        range="Scores!A1",
        valueInputOption="RAW",
        body={"values": [["Player", "Points", "Time (ms)", "When (UTC)"]]}
    ).execute()