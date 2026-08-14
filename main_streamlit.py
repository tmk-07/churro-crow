import streamlit as st

from ui_shared import app_chrome


app_chrome()

navigation = st.navigation(
    [
        st.Page("pages/learn.py", title="Learn", icon="📘", default=True),
        st.Page("pages/check.py", title="Check", icon="✅"),
        st.Page("pages/solve.py", title="Solve", icon="🧩"),
        st.Page("pages/practice.py", title="Practice", icon="🛠️"),
        st.Page("pages/leaderboards.py", title="Leaderboards", icon="🏆"),
    ],
    position="sidebar",
)
navigation.run()
