# z_leaderboard.py
import sqlite3, os
from datetime import datetime, timezone
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "leaderboard.db")

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Better concurrency defaults
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            points INTEGER NOT NULL,
            time_ms INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def add_score(username: str, points: int, time_ms: int):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO scores (username, points, time_ms, created_at) VALUES (?, ?, ?, ?)",
        (username, points, time_ms, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    # Bust any cached leaderboard data
    try:
        get_leaderboard.clear()
    except Exception:
        pass
    return cur.lastrowid

# ⛔ Remove caching here to eliminate stale reads during debugging.
#    You can add @st.cache_data back later if you want.
def get_leaderboard(limit=20):
    conn = get_conn()
    return conn.execute("""
        SELECT username, points, time_ms, created_at
        FROM scores
        ORDER BY points DESC, time_ms ASC, created_at ASC
        LIMIT ?
    """, (limit,)).fetchall()

def leaderboard_page():
    st.title("🏆 Leaderboard")
    st.caption(f"DB path: {DB_PATH}")

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

    c1, c2, c3 = st.columns(3)
    if c1.button("⬅ Back to Home"):
        st.session_state.page = "start"
        st.rerun()
    if c2.button("🔁 Refresh"):
        st.rerun()
    if c3.button("➕ Insert test row"):
        add_score("TestUser", 1, 1234)
        st.success("Inserted TestUser(1)")
        st.rerun()
