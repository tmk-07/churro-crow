# z_leaderboard.py
import sqlite3
import time
from datetime import datetime, timezone
import streamlit as st

# ---- DB helpers ----
@st.cache_resource
def get_conn():
    conn = sqlite3.connect("leaderboard.db", check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            points INTEGER NOT NULL,
            time_ms INTEGER NOT NULL,         -- lower = faster
            created_at TEXT NOT NULL          -- ISO timestamp (UTC)
        )
    """)
    conn.commit()
    return conn

def add_score(username: str, points: int, time_ms: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO scores (username, points, time_ms, created_at) VALUES (?, ?, ?, ?)",
        (username, points, time_ms, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()

@st.cache_data(ttl=10)
def get_leaderboard(limit=20):
    conn = get_conn()
    return conn.execute("""
        SELECT username, points, time_ms, created_at
        FROM scores
        ORDER BY points DESC, time_ms ASC, created_at ASC
        LIMIT ?
    """, (limit,)).fetchall()

# ---- Page UI ----
def leaderboard_page():
    st.title("🏆 Leaderboard")
    rows = get_leaderboard(20)

    if rows:
        st.dataframe(
            {
                "#": list(range(1, len(rows)+1)),
                "Player": [r[0] for r in rows],
                "Points": [r[1] for r in rows],
                "Time (s)": [round(r[2] / 1000, 2) for r in rows],
                "When (UTC)": [r[3] for r in rows],
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No scores yet — be the first!")

    c1, c2 = st.columns(2)
    if c1.button("⬅ Back to Home"):
        st.session_state.page = "start"
        st.rerun()
    if c2.button("🔁 Refresh"):
        get_leaderboard.clear()
        st.rerun()
