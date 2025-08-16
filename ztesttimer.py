import streamlit as st
import os

def ztesttimer():
    st.title("⏱ Timer Test")

    # Path to your timer video
    video_path = os.path.join("assets", "timers", "60s.mp4")

    if os.path.exists(video_path):
        st.video(os.path.join("assets", "timers", "60s.mp4"), format="video/mp4", start_time=0)
    else:
        st.error("⚠️ Timer video not found. Make sure 60s.mp4 is in assets/timers/")
