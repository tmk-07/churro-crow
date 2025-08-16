# ztesttimer.py
import os
import time
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="Timer Test", page_icon="⏱️", layout="centered")

# ========= Settings =========
TIMER_SECONDS = 60          # change to 10 while testing
VIDEO_PATH = "assets/timers/60s.mp4"  # put your clip here (optional)
# ===========================

def ensure_state():
    defaults = {
        "timer_started": False,
        "timer_end_ts": None,
        "use_video": True,     # default to video; will fall back if file missing
        "last_tick": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

ensure_state()

st.title("Timer Test")
st.caption("This page can show either a real video countdown (MP4) or a built-in HTML countdown.")

# Let the user pick which mode before starting
if not st.session_state.timer_started:
    # If the video file does not exist, force fallback to HTML
    have_video = Path(VIDEO_PATH).is_file()
    st.session_state.use_video = st.toggle(
        "Use video clip (fallback to HTML if file missing)",
        value=True if have_video else False,
        help="Upload your clip to assets/timers/60s.mp4"
    )
    if st.session_state.use_video and not have_video:
        st.info(f"Video not found at `{VIDEO_PATH}`. Will show the HTML countdown instead.")

    col1, col2 = st.columns(2)
    with col1:
        secs = st.number_input("Timer length (seconds)", min_value=5, max_value=600, value=TIMER_SECONDS, step=5)
    with col2:
        st.write("")
        st.write("")
        if st.button("Start Timer", use_container_width=True):
            st.session_state.timer_started = True
            st.session_state.timer_end_ts = time.time() + int(secs)
            st.session_state.last_tick = 0.0
            st.rerun()

# When running
else:
    # Compute time left using UNIX seconds
    end_ts = st.session_state.timer_end_ts or time.time()
    time_left = max(int(end_ts - time.time()), 0)

    # Big numeric header
    mm = time_left // 60
    ss = time_left % 60
    st.subheader(f"⏱️ Time left: {mm:02d}:{ss:02d}")

    # --- Visual: either video clip or HTML/CSS/JS countdown ---
    if st.session_state.use_video and Path(VIDEO_PATH).is_file():
        # Use a raw HTML <video> so we can force autoplay/muted/inline.
        # This is just a visual; actual timing is driven above by end_ts.
        components.html(
            f"""
            <video
              src="{VIDEO_PATH}"
              autoplay
              muted
              playsinline
              style="width:100%; border-radius:12px; outline:none"
              oncontextmenu="return false">
            </video>
            """,
            height=250,
        )
        st.caption("Playing your video clip.")
    else:
        # Built-in HTML/CSS/JS countdown (no assets)
        # Runs entirely in the browser; Streamlit’s own timer above is still the source of truth.
        components.html(
            f"""
            <div style="display:flex;align-items:center;justify-content:center;height:240px;">
              <div id="timer"
                   style="font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
                          font-size:72px; font-weight:800; letter-spacing:2px;">
                {mm:02d}:{ss:02d}
              </div>
            </div>
            <script>
              (function() {{
                const endTs = {int(end_ts*1000)};
                const pad = (n)=> String(n).padStart(2,'0');
                const el = document.getElementById('timer');
                function tick(){{
                  const now = Date.now();
                  const msLeft = Math.max(endTs - now, 0);
                  const t = Math.floor(msLeft/1000);
                  const m = Math.floor(t/60);
                  const s = t % 60;
                  if (el) el.textContent = pad(m)+":"+pad(s);
                  if (msLeft <= 0) clearInterval(iv);
                }}
                tick();
                const iv = setInterval(tick, 200);
              }})();
            </script>
            """,
            height=260,
        )
        st.caption("HTML countdown (no video file needed).")

    # When time hits 0, show next actions
    if time_left == 0:
        st.success("⏰ Time's up!")
        c1, c2 = st.columns(2)
        if c1.button("Restart", use_container_width=True):
            st.session_state.timer_started = False
            st.session_state.timer_end_ts = None
            st.rerun()
        if c2.button("Close", use_container_width=True):
            st.session_state.timer_started = False
            st.session_state.timer_end_ts = None
            st.rerun()
    else:
        # Gentle tick ~2x/second. This drives the numeric header above.
        if time.time() - st.session_state.last_tick > 0.5:
            st.session_state.last_tick = time.time()
            st.rerun()
