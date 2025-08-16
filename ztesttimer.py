import streamlit as st
import os

def ztesttimer():
    st.title("⏱ Timer Test 0 ")

    video_path = os.path.join("assets", "timers", "60s.mp4")

    if os.path.exists(video_path):
        st.markdown(
            f"""
            <video autoplay muted playsinline width="100%">
                <source src="{os.path.join("assets", "timers", "60s.mp4")}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error("⚠️ Timer video not found. Make sure 60s.mp4 is in assets/timers/")

    st.button("back to start", on_click=lambda: st.session_state.update(page="start"))
