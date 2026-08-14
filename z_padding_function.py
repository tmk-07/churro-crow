import os
import random
import time

import streamlit as st

from leaderboard_store import LeaderboardConfigurationError, append_score


RESTRICTION_QUESTIONS = [
    ("R ⊆ R", "z"), ("B ⊆ B", "z"), ("G ⊆ G", "z"), ("Y ⊆ Y", "z"),
    ("R ⊆ V", "z"), ("R ⊆ Z", "r"), ("B ⊆ V", "z"), ("B ⊆ Z", "b"),
    ("Y ⊆ V", "z"), ("Y ⊆ Z", "y"), ("G ⊆ V", "z"), ("G ⊆ Z", "g"),
    ("B ⊆ B'", "b"), ("R ⊆ R'", "r"), ("Y ⊆ Y'", "y"), ("G ⊆ G'", "g"),
    ("B' ⊆ B", "b'"), ("R' ⊆ R", "r'"), ("Y' ⊆ Y", "y'"), ("G' ⊆ G", "g'"),
    ("B' = B", "v"), ("R' = R", "v"), ("Y' = Y", "v"), ("G' = G", "v"),
    ("V = Z", "v"), ("V ⊆ Z", "v"), ("Z ⊆ V", "z"),
    ("Z ⊆ B", "z"), ("Z ⊆ R", "z"), ("Z ⊆ Y", "z"), ("Z ⊆ G", "z"),
    ("Z = B", "b"), ("Z = R", "r"), ("Z = G", "g"), ("Z = Y", "y"),
]

SYMDIFF_QUESTIONS = [
    ("V ∩ B", "b"), ("V ∩ R", "r"), ("V ∩ G", "g"), ("V ∩ Y", "y"),
    ("V ∪ B", "v"), ("V ∪ R", "v"), ("V ∪ G", "v"), ("V ∪ Y", "v"),
    ("B ∪ B'", "v"), ("R' ∪ R", "v"), ("G ∪ G'", "v"), ("Y ∪ Y'", "v"),
    ("B' ∩ B", "z"), ("R ∩ R'", "z"), ("G' ∩ G", "z"), ("Y ∩ Y'", "z"),
    ("B - B", "z"), ("R - R", "z"), ("G - G", "z"), ("Y - Y", "z"),
    ("B - B'", "v"), ("R - R'", "v"), ("G - G'", "v"), ("Y - Y'", "v"),
    ("B' - B", "v"), ("R' - R", "v"), ("G' - G", "v"), ("Y' - Y", "v"),
    ("V - B", "b'"), ("V - R", "r'"), ("V - G", "g'"), ("V - Y", "y'"),
    ("Z - B", "b"), ("Z - R", "r"), ("Z - G", "g"), ("Z - Y", "y"),
    ("V - Z", "v"), ("Z - V", "v"), ("V ∩ Z", "z"), ("Z ∪ V", "v"),
]

SET_QUESTIONS = [
    ("V ∩ B", "b"), ("V ∩ R", "r"), ("V ∩ G", "g"), ("V ∩ Y", "y"),
    ("V ∪ B", "v"), ("V ∪ R", "v"), ("V ∪ G", "v"), ("V ∪ Y", "v"),
    ("B ∪ B'", "v"), ("R' ∪ R", "v"), ("G ∪ G'", "v"), ("Y ∪ Y'", "v"),
    ("B' ∩ B", "z"), ("R ∩ R'", "z"), ("G' ∩ G", "z"), ("Y ∩ Y'", "z"),
    ("B - B", "z"), ("R - R", "z"), ("G - G", "z"), ("Y - Y", "z"),
    ("B - B'", "b"), ("R - R'", "r"), ("G - G'", "g"), ("Y - Y'", "y"),
    ("B' - B", "b'"), ("R' - R", "r'"), ("G' - G", "g'"), ("Y' - Y", "y'"),
    ("V - B", "b'"), ("V - R", "r'"), ("V - G", "g'"), ("V - Y", "y'"),
    ("Z - B", "z"), ("Z - R", "z"), ("Z - G", "z"), ("Z - Y", "z"),
    ("V - Z", "v"), ("Z - V", "z"), ("V ∩ Z", "z"), ("Z ∪ V", "v"),
]

MODE_QUESTIONS = {
    "Padding Practice": SET_QUESTIONS,
    "Restriction Practice": RESTRICTION_QUESTIONS,
    "Padding (w/ SymDiff)": SYMDIFF_QUESTIONS,
}


def _initialize_state():
    defaults = {
        "quiz_active": False,
        "show_results": False,
        "end_ts": None,
        "score": 0,
        "current_q": None,
        "feedback": None,
        "question_counter": 0,
        "username": "",
        "start_ms": 0,
        "quiz_mode": "Padding Practice",
        "last_tick": 0.0,
        "score_saved": False,
        "timer_start_ts": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def padding_practice():
    _initialize_state()

    if not st.session_state.quiz_active and not st.session_state.show_results:
        st.session_state.quiz_mode = st.selectbox(
            "Choose a mode",
            tuple(MODE_QUESTIONS),
            key="mode_select",
        )

    questions = MODE_QUESTIONS[st.session_state.quiz_mode]

    def start_quiz():
        now = time.time()
        st.session_state.quiz_active = True
        st.session_state.show_results = False
        st.session_state.end_ts = now + 60
        st.session_state.timer_start_ts = now
        st.session_state.start_ms = int(now * 1000)
        st.session_state.score = 0
        st.session_state.current_q = random.choice(questions)
        st.session_state.feedback = None
        st.session_state.question_counter = 0
        st.session_state.score_saved = False

    def check_answer(user_answer: str):
        answer = user_answer.strip().lower()
        if not answer:
            st.session_state.feedback = ("Please enter an answer", "warning")
        elif answer == st.session_state.current_q[1]:
            st.session_state.score += 1
            st.session_state.feedback = ("Correct!", "success")
            st.session_state.current_q = random.choice(questions)
            st.session_state.question_counter += 1
        else:
            st.session_state.feedback = ("Wrong.", "error")

    st.title("OS Quick Padding Practice")
    st.write(
        "You have one minute. For restrictions mode, answer with the "
        "eliminated set name. 'z' represents null."
    )

    if st.session_state.show_results:
        st.subheader(f"Your score: {st.session_state.score} points")

        if not st.session_state.score_saved:
            if st.button("💾 Submit Score to Leaderboard", key="submit_score_btn"):
                try:
                    with st.spinner("Writing to sheet..."):
                        append_score(
                            st.session_state.username,
                            st.session_state.score,
                            st.session_state.quiz_mode,
                        )
                except LeaderboardConfigurationError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("The score could not be saved. Please try again later.")
                else:
                    st.session_state.score_saved = True
                    st.success("✅ Score submitted to leaderboard!")

        play_again, leaderboard = st.columns(2)
        if play_again.button("Play Again", key="play_again_btn"):
            start_quiz()
            st.rerun()
        if leaderboard.button("🏆 View Leaderboard", key="view_leaderboard_quiz_btn"):
            st.session_state.page = "leaderboard"
            st.rerun()
        if st.button("Back to Home", key="bottom_home_btn_results"):
            st.session_state.page = "start"
            st.rerun()
        return

    if not st.session_state.quiz_active:
        st.session_state.username = st.text_input(
            "Enter name (opt):",
            value=st.session_state.username,
            autocomplete="off",
            max_chars=40,
            key="name_input",
        )
        start, leaderboard, home = st.columns(3)
        if start.button("Start Quiz", use_container_width=True, key="start_quiz_btn"):
            start_quiz()
            st.rerun()
        if leaderboard.button("🏆 View Leaderboard", key="view_leaderboard_btn_main"):
            st.session_state.page = "leaderboard"
            st.rerun()
        if home.button("Back to Home", key="home_btn_main"):
            st.session_state.page = "start"
            st.rerun()
        return

    time_left = max(int(st.session_state.end_ts - time.time()), 0)
    if time_left == 0:
        st.session_state.quiz_active = False
        st.session_state.show_results = True
        st.rerun()

    elapsed = time.time() - st.session_state.timer_start_ts
    timer_video = os.path.join("assets", "timers", "60s.mp4")
    if os.path.exists(timer_video):
        left, middle, right = st.columns([1, 2, 1])
        with middle:
            st.video(
                timer_video,
                format="video/mp4",
                start_time=int(max(0, min(60, elapsed))),
                muted=True,
                autoplay=True,
            )
    else:
        st.subheader(f"⏱️ Time left: {time_left:02d}s")

    st.subheader(f"Question: {st.session_state.current_q[0]} ?")
    with st.form(f"answer_form_{st.session_state.start_ms}", clear_on_submit=True):
        answer = st.text_input(
            "Your answer:",
            autocomplete="off",
            key=f"answer_input_{st.session_state.start_ms}",
        )
        if st.form_submit_button("Submit"):
            check_answer(answer)

    if st.session_state.feedback:
        message, kind = st.session_state.feedback
        renderer = {
            "success": st.success,
            "error": st.error,
            "warning": st.warning,
        }[kind]
        renderer(message)

    if st.session_state.quiz_active and time.time() - st.session_state.last_tick > 0.5:
        st.session_state.last_tick = time.time()
        st.rerun()

    if st.button("Back to Home", key="bottom_home_btn"):
        st.session_state.page = "start"
        st.rerun()
