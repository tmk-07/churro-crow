import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime, timezone
import time

# ==============================================================
# HARDCODED SHEET + SERVICE ACCOUNT INFO
# ==============================================================
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

# ==============================================================
# GOOGLE SHEETS SERVICE
# ==============================================================
@st.cache_resource
def get_sheet_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build('sheets', 'v4', credentials=creds)

# ==============================================================
# FUNCTIONS
# ==============================================================
def get_leaderboard(limit=20):
    try:
        service = get_sheet_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range="Scores!A:C"
        ).execute()
        values = result.get('values', [])
        return values[1:] if len(values) > 1 else []
    except Exception as e:
        st.error(f"Error loading leaderboard: {str(e)}")
        return []

def add_score(username: str, points: int):  # Remove time_ms parameter
    try:
        service = get_sheet_service()
        # Use simple date format instead of full timestamp
        date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        # Only 3 values now: username, points, date
        values = [[username, points, date_str]]
        body = {'values': values}
        # Update range to A:C (3 columns)
        result = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range="Scores!A:C",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        
        st.success(f"Score added successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to save score: {str(e)}")
        return False

# MODIFIED get_leaderboard function to accept mode parameter
def get_leaderboard(mode="SetOperations", limit=5):
    """Get top scores for a specific mode"""
    try:
        service = get_sheet_service()
        # Map mode to sheet name
        sheet_name = {
            "Restriction Practice": "Restriction",
            "Padding Practice": "SetOperations",
            "Padding (w/ SymDiff)": "SymDiff"
        }.get(mode, "SetOperations")  # default to SetOperations
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"{sheet_name}!A:C"
        ).execute()
        values = result.get('values', [])
        return values[1:] if len(values) > 1 else []
    except Exception as e:
        st.error(f"Error loading {mode} leaderboard: {str(e)}")
        return []

# MODIFIED leaderboard_page function to show all 3 leaderboards
def leaderboard_page():
    st.title("🏆 Leaderboards")
    
    # Define quiz modes and their display names. display names are the keys
    modes = {
        "Padding Practice": "Padding Practice",
        "Restriction Practice": "Restrictions",
        "Padding (w/ SymDiff)": "SymDiff Padding"
    }
    
    # Create 3 columns for the leaderboards
    cols = st.columns(3)
    
    for i, (mode, title) in enumerate(modes.items()):
        with cols[i]:
            st.subheader(title)
            scores = get_leaderboard(mode)
            
            if scores:
                df = pd.DataFrame(scores, columns=["Player", "Points", "Date"])
                df["Points"] = pd.to_numeric(df["Points"], errors="coerce").fillna(0).astype(int)
                df = df.sort_values(by=["Points", "Date"], ascending=[False, False])
                top_5 = df.head(5)
                
                # Display with ranking
                st.dataframe(top_5[["Player", "Points", "Date"]], hide_index=True)
            else:
                st.info("No scores yet")
    
    # Back and refresh buttons
    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("⬅ Back to Home", key="home_btn"):
        st.session_state.page = "start"
        st.rerun()
    if c2.button("🔁 Refresh Leaderboards", key="refresh_btn"):
        st.rerun()

def init_sheet():
    try:
        service = get_sheet_service()
        service.spreadsheets().values().clear(
            spreadsheetId=SHEET_ID,
            range="Scores!A:C",  # Update to A:C
            body={}
        ).execute()
        # Update to 3-column header
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range="Scores!A1",
            valueInputOption="RAW",
            body={"values": [["Player", "Points", "Date"]]}  # 3 columns
        ).execute()
        st.success("Sheet initialized successfully!")
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.error(f"Initialization failed: {str(e)}")
