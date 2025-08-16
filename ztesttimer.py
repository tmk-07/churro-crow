import uuid
import streamlit.components.v1 as components

def render_countdown_video(run_id: str):
    """
    Shows a muted, autoplaying 60s countdown video.
    Query param (?rid=...) forces a fresh load when a new quiz starts.
    """
    src = f"assets/countdown_60.mp4?rid={run_id}"
    components.html(
        f"""
        <video width="100%" height="80" autoplay muted playsinline style="outline:none" oncontextmenu="return false;">
          <source src="{src}" type="video/mp4">
          Your browser does not support the video tag.
        </video>
        """,
        height=90,
    )
