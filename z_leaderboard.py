import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timezone
import time
import os

# =================================================================
# HARDCODED SOLUTION - BYPASSES SECRETS ISSUE
# =================================================================
HARDCODED_SHEET_ID = "1IHC4Ju76c-ftIYiLEZlrb_n1tEVzbzXrSJYVlb6Qht4"

def get_sheet_id():
    """Always return the hardcoded sheet ID"""
    return HARDCODED_SHEET_ID

# Use this everywhere instead of st.secrets
SHEET_ID = get_sheet_id()
# =================================================================

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
            spreadsheetId=SHEET_ID,  # Use constant here
            range="Scores!A:D"
        ).execute()
        values = result.get('values', [])
        return values[1:] if len(values) > 1 else []
    except Exception as e:
        st.error(f"Error loading leaderboard: {str(e)}")
        return []

def add_score(username: str, points: int, time_ms: int):
    try:
        service = get_sheet_service()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        values = [[username, points, time_ms, timestamp]]
        body = {'values': values}
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,  # Use constant here
            range="Scores",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        
        # Debug output
        st.success(f"Score added to Sheet ID: {SHEET_ID}")
        st.write(f"Sheet update result: {result}")
        return True
    except Exception as e:
        st.error(f"Failed to save score: {str(e)}")
        return False

def leaderboard_page():
    st.title("🏆 Leaderboard")
    
    # Display sheet info with direct link
    st.subheader(f"Using Google Sheet: {SHEET_ID}")
    st.link_button("Open Google Sheet", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    
    # Display leaderboard
    scores = get_leaderboard()
    if scores:
        df = pd.DataFrame(scores, columns=["Player", "Points", "Time (ms)", "When (UTC)"])
        df["Points"] = df["Points"].astype(int)
        df["Time (s)"] = (df["Time (ms)"].astype(int) / 1000).round(2)
        df = df.sort_values(by=["Points", "Time (ms)"], ascending=[False, True])
        st.dataframe(df[["Player", "Points", "Time (s)", "When (UTC)"]], hide_index=True)
    else:
        st.info("No scores yet - be the first!")

    # Navigation buttons
    c1, c2 = st.columns(2)
    if c1.button("⬅ Back to Home", key="home_btn"):
        st.session_state.page = "start"
        st.rerun()
    if c2.button("🔁 Refresh Leaderboard", key="refresh_btn"):
        st.rerun()

def init_sheet():
    try:
        service = get_sheet_service()
        # Clear existing data
        service.spreadsheets().values().clear(
            spreadsheetId=SHEET_ID,
            range="Scores!A:Z",
            body={}
        ).execute()
        
        # Add headers
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range="Scores!A1",
            valueInputOption="RAW",
            body={"values": [["Player", "Points", "Time (ms)", "When (UTC)"]]}
        ).execute()
        st.success("Sheet initialized successfully!")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.error(f"Initialization failed: {str(e)}")