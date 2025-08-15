import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid
import random
import time
import sqlite3
from datetime import datetime, timedelta, timezone
import z_leaderboard as lb



resquestions = [
        ("R ⊆ R", 'z'),
        ("B ⊆ B", 'z'),
        ("G ⊆ G", 'z'),
        ("Y ⊆ Y", 'z'),

        ("R ⊆ V", 'z'),
        ("R ⊆ Z", 'r'),
        ("B ⊆ V", 'z'),
        ("B ⊆ Z", 'b'),
        ("Y ⊆ V", 'z'),
        ("Y ⊆ Z", 'y'),
        ("G ⊆ V", 'z'),
        ("G ⊆ Z", 'g'),

        ("B ⊆ B'", 'b'),
        ("R ⊆ R'", 'r'),
        ("Y ⊆ Y'", 'y'),
        ("G ⊆ G'", 'g'),

        ("B' ⊆ B", "b'"),
        ("R' ⊆ R", "r'"),
        ("Y' ⊆ Y", "y'"),
        ("G' ⊆ G", "g'"),

        ("B' = B", "v"),
        ("R' = R", "v"),
        ("Y' = Y", "v"),
        ("G' = G", "v"),

        ("V = Z", "v"),
        ("V ⊆ Z", "v"),
        ("Z ⊆ V", "z"),

        ("Z ⊆ B", "z"),
        ("Z ⊆ R", "z"),
        ("Z ⊆ Y", "z"),
        ("Z ⊆ G", "z"),

        ("Z = B", "b"),
        ("Z = R", "r"),
        ("Z = G", "g"),
        ("Z = Y", "y"),

    ]

symquestions = [
        ("V ∩ B", 'b'),
        ("V ∩ R", 'r'),
        ("V ∩ G", 'g'),
        ("V ∩ Y", 'y'),

        ("V ∪ B", 'v'),
        ("V ∪ R", 'v'),
        ("V ∪ G", 'v'),
        ("V ∪ Y", 'v'),

        ("B ∪ B'", 'v'),
        ("R' ∪ R", 'v'),
        ("G ∪ G'", 'v'),
        ("Y' ∪ Y'", 'v'),

        ("B' ∩ B", 'z'),
        ("R ∩ R'", 'z'),
        ("G' ∩ G", 'z'),
        ("Y ∩ Y'", 'z'),

        ("B - B", 'z'),
        ("R - R", 'z'),
        ("G - G", 'z'),
        ("Y - Y", 'z'),

        ("B - B'", 'v'),
        ("R - R'", 'v'),
        ("G - G'", 'v'),
        ("Y - Y'", 'v'),

        ("B' - B", "v"),
        ("R' - R", "v"),
        ("G' - G", "v"),
        ("Y' - Y", "v"),

        ("V - B", "b'"),
        ("V - R", "r'"),
        ("V - G", "g'"),
        ("V - Y", "y'"),

        ("Z - B", 'b'),
        ("Z - R", 'r'),
        ("Z - G", 'g'),
        ("Z - Y", 'y'),

        ("V - Z", 'v'),
        ("Z - V", 'v'),
        ("V ∩ Z", 'z'),
        ("Z ∪ V", 'v'),



]

setquestions = [
        ("V ∩ B", 'b'),
        ("V ∩ R", 'r'),
        ("V ∩ G", 'g'),
        ("V ∩ Y", 'y'),

        ("V ∪ B", 'v'),
        ("V ∪ R", 'v'),
        ("V ∪ G", 'v'),
        ("V ∪ Y", 'v'),

        ("B ∪ B'", 'v'),
        ("R' ∪ R", 'v'),
        ("G ∪ G'", 'v'),
        ("Y ∪ Y'", 'v'),

        ("B' ∩ B", 'z'),
        ("R ∩ R'", 'z'),
        ("G' ∩ G", 'z'),
        ("Y ∩ Y'", 'z'),

        ("B - B", 'z'),
        ("R - R", 'z'),
        ("G - G", 'z'),
        ("Y - Y", 'z'),

        ("B - B'", 'b'),
        ("R - R'", 'r'),
        ("G - G'", 'g'),
        ("Y - Y'", 'y'),

        ("B' - B", "b'"),
        ("R' - R", "r'"),
        ("G' - G", "g'"),
        ("Y' - Y", "y'"),

        ("V - B", "b'"),
        ("V - R", "r'"),
        ("V - G", "g'"),
        ("V - Y", "y'"),

        ("Z - B", 'z'),
        ("Z - R", 'z'),
        ("Z - G", 'z'),
        ("Z - Y", 'z'),

        ("V - Z", 'v'),
        ("Z - V", 'z'),
        ("V ∩ Z", 'z'),
        ("Z ∪ V", 'v'),



]


def padding_practice():
    # Initialize session state - ADDED LAST_TIMER_UPDATE
    if 'quiz_active' not in st.session_state:
        st.session_state.quiz_active = False
    if 'end_time' not in st.session_state:
        st.session_state.end_time = None
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'current_q' not in st.session_state:
        st.session_state.current_q = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'last_rerun' not in st.session_state:
        st.session_state.last_rerun = time.time()
    if 'question_counter' not in st.session_state:
        st.session_state.question_counter = 0
    if 'last_timer_update' not in st.session_state:  # ADD THIS
        st.session_state.last_timer_update = time.time()
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'start_ms' not in st.session_state:
        st.session_state.start_ms = 0
   


    def start_quiz():
        st.session_state.quiz_active = True
        st.session_state.end_time = datetime.now() + timedelta(seconds=20)
        st.session_state.start_ms = int(time.time() * 1000)  # ADD
        st.session_state.score = 0
        st.session_state.current_q = random.choice(questions)
        st.session_state.feedback = None
        st.session_state.question_counter = 0
        st.session_state.last_rerun = time.time()
        st.session_state.last_timer_update = time.time()



    def check_answer(user_answer):
        if not user_answer.strip():
            st.session_state.feedback = ("Please enter an answer", "warning")
            return
        user_answer_lower = user_answer.strip().lower() 
        if user_answer_lower.strip() == st.session_state.current_q[1]:
            st.session_state.score += 1
            st.session_state.feedback = ("Correct!", "success")
            # Move to next question
            st.session_state.current_q = random.choice(questions)
            st.session_state.question_counter += 1
        else:
            st.session_state.feedback = (f"Wrong.", "error")

    # Main app layout
    st.title("OS Quick Padding Practice")
    
    qopt = st.selectbox("Choose a mode", ("Padding Practice","Restriction Practice","Padding (w/ SymDiff)"))
    if qopt == "Padding Practice":
        questions = setquestions
    elif qopt == "Restriction Practice":
        questions = resquestions
    elif qopt == "Padding (w/ SymDiff)":
        questions = symquestions

    st.write("You have two minutes. For restrictions mode, answer with the eliminated set name. 'z' represents null")


    # Start quiz button
        # Start quiz screen (when not active)
    if not st.session_state.quiz_active:
        st.session_state.username = st.text_input(
            "Enter your name (for the leaderboard):",
            value=st.session_state.username
        )

        c1, c2, c3 = st.columns(3)
        if c1.button("Start Quiz"):
            if not st.session_state.username.strip():
                st.warning("Please enter your name to start.")
            else:
                start_quiz()

        if c2.button("🏆 View Leaderboard"):
            st.session_state.page = "leaderboard"
            st.rerun()

        if c3.button("back to home"):
            st.session_state.page = "start"
            st.rerun()

        st.stop()


    # Timer logic
    now = datetime.now()
    time_left = max((st.session_state.end_time - now).total_seconds(), 0)

    # Display timer
    if time_left > 0:
        timer_placeholder = st.empty()
        timer_text = f"⏱️ Time left: {int(time_left//60):02d}:{int(time_left%60):02d}"
        timer_placeholder.subheader(timer_text)

    # Quiz ended when time's up
    if time_left <= 0:
        st.session_state.quiz_active = False
        st.balloons()
        st.subheader(f"⏰ Time's up! Final Score: {st.session_state.score}")

        # elapsed time in ms
        elapsed_ms = (int(time.time() * 1000) - st.session_state.start_ms) if st.session_state.start_ms else 120_000

        if st.button("💾 Submit Score to Leaderboard"):
            lb.add_score(st.session_state.username or "Player",
                    st.session_state.score,
                    elapsed_ms)
            lb.get_leaderboard.clear()   # ← invalidate cached rows immediately
            st.success("Score saved!")

        c1, c2, c3 = st.columns(3)
        if c1.button("🏆 View Leaderboard"):
            st.session_state.page = "leaderboard"
            st.rerun()

        if c2.button("Play Again"):
            start_quiz()

        if c3.button("Back to Home"):
            st.session_state.page = "start"
            st.rerun()

        st.stop()


        

    # Display current question
    st.subheader(f"Question: {st.session_state.current_q[0]} ?")

    # FIXED THE INPUT FIELD
    with st.form("answer_form", clear_on_submit=True):
        # Text input for the answer
        answer = st.text_input("Your answer:", value="")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            check_answer(answer)

    # Show feedback if exists
    if st.session_state.feedback:
        message, type = st.session_state.feedback
        if type == "success":
            st.success(message)
        elif type == "error":
            st.error(message)
        else:
            st.warning(message)

    # ADDED PROPER TIMER UPDATE LOGIC
    current_time = time.time()
    if current_time - st.session_state.last_timer_update > 0.5:
        st.session_state.last_timer_update = current_time
        st.rerun()

    st.write("The timer is kinda buggy")

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()



    