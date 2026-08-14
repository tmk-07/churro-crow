import pandas as pd
import streamlit as st

from leaderboard_store import LeaderboardConfigurationError, read_scores


MODES = {
    "Padding Practice": "Padding Practice",
    "Restriction Practice": "Restrictions",
    "Padding (w/ SymDiff)": "SymDiff Padding",
}


def _top_scores(scores: list[list[str]], limit: int = 5) -> pd.DataFrame:
    rows = [row[:3] + [""] * max(0, 3 - len(row)) for row in scores]
    frame = pd.DataFrame(rows, columns=["Player", "Points", "Date"])
    frame["Player"] = frame["Player"].astype(str).fillna("").str.strip()
    frame["Points"] = pd.to_numeric(
        frame["Points"], errors="coerce"
    ).fillna(0).astype(int)
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.sort_values(["Points", "Date"], ascending=[False, False])
    frame["PlayerKey"] = frame["Player"].str.casefold()
    frame = frame.drop_duplicates("PlayerKey", keep="first")
    frame = frame.head(limit).copy()
    frame["Date"] = frame["Date"].dt.strftime("%Y-%m-%d").fillna("")
    return frame[["Player", "Points", "Date"]]


def leaderboard_page():
    st.title("🏆 Leaderboards")
    columns = st.columns(3)

    for column, (mode, title) in zip(columns, MODES.items()):
        with column:
            st.subheader(title)
            try:
                scores = read_scores(mode)
            except LeaderboardConfigurationError as exc:
                st.info(str(exc))
                continue
            except Exception:
                st.error("The leaderboard is temporarily unavailable.")
                continue

            if scores:
                st.dataframe(_top_scores(scores), hide_index=True)
            else:
                st.info("No scores yet")

    st.markdown("---")
    back, refresh = st.columns(2)
    if back.button("⬅ Back to Home", key="home_btn"):
        st.session_state.page = "start"
        st.rerun()
    if refresh.button("🔁 Refresh Leaderboards", key="refresh_btn"):
        st.cache_resource.clear()
        st.rerun()
