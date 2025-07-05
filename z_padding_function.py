import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid
import random
import time
from datetime import datetime, timedelta

resquestions = [
        ("R c R", 'z'),
        ("B c B", 'z'),
        ("G c G", 'z'),
        ("Y c Y", 'z'),

        ("R c V", 'z'),
        ("R c Z", 'r'),
        ("B c V", 'z'),
        ("B c Z", 'b'),
        ("Y c V", 'z'),
        ("Y c Z", 'y'),
        ("G c V", 'z'),
        ("G c Z", 'g'),

        ("B c B'", 'b'),
        ("R c R'", 'r'),
        ("Y c Y'", 'y'),
        ("G c G'", 'g'),

        ("B' c B", "b'"),
        ("R' c R", "r'"),
        ("Y' c Y", "y'"),
        ("G' c G", "g'"),

        ("B' = B", "v"),
        ("R' = R", "v"),
        ("Y' = Y", "v"),
        ("G' = G", "v"),

        ("V = Z", "v"),
        ("V c Z", "v"),
        ("Z c V", "z"),

        ("Z c B", "z"),
        ("Z c R", "z"),
        ("Z c Y", "z"),
        ("Z c G", "z"),

        ("Z = B", "b"),
        ("Z = R", "r"),
        ("Z = G", "g"),
        ("Z = Y", "y"),

    ]

setquestions = [
        ("V n B", 'b'),
        ("V n R", 'r'),
        ("V n G", 'g'),
        ("V n Y", 'y'),

        ("V u B", 'v'),
        ("V u R", 'v'),
        ("V u G", 'v'),
        ("V u Y", 'v'),

]

def padding_practice():

    # Initialize session state
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

    # Question bank - (question, answer) pairs
    questions = resquestions

    def start_quiz():
        st.session_state.quiz_active = True
        st.session_state.end_time = datetime.now() + timedelta(seconds=120)
        st.session_state.score = 0
        st.session_state.current_q = random.choice(questions)
        st.session_state.feedback = None
        st.session_state.question_counter = 0
        st.session_state.last_rerun = time.time()

    def check_answer(user_answer):
        try:
            if user_answer is None or user_answer == "":
                st.session_state.feedback = ("Please enter an answer", "warning")
                return
                
            user_num = int(user_answer)
            if user_num == st.session_state.current_q[1]:
                st.session_state.score += 1
                st.session_state.feedback = ("Correct!", "success")
                # Move to next question
                st.session_state.current_q = random.choice(questions)
                st.session_state.question_counter += 1
            else:
                st.session_state.feedback = ("Wrong! Try again.", "error")
        except ValueError:
            st.session_state.feedback = ("Please enter a valid number", "warning")

    # Main app layout
    st.title("2-Minute Padding Quiz")
    st.write("You have two minutes. For restrictions mode, answer with the eliminated set name. 'z' represents null")

    # Start quiz button
    if not st.session_state.quiz_active:
        st.button("Start Quiz", on_click=start_quiz)
        st.stop()

    # Timer logic
    now = datetime.now()
    time_left = max((st.session_state.end_time - now).total_seconds(), 0)

    # Display timer
    timer_placeholder = st.empty()
    timer_placeholder.subheader(f"⏱️ Time left: {int(time_left//60):02d}:{int(time_left%60):02d}")

    # Quiz ended when time's up
    if time_left <= 0:
        st.session_state.quiz_active = False
        st.balloons()
        st.subheader(f"⏰ Time's up! Final Score: {st.session_state.score}")
        st.write(f"Total questions attempted: {st.session_state.question_counter}")
        if st.button("Play Again"):
            start_quiz()
        st.stop()

    # Display current question
    st.subheader(f"Question: {st.session_state.current_q[0]} = ?")

    # Answer input with form for Enter key support
    with st.form("answer_form", clear_on_submit=True):
        # Empty input with no placeholder
        answer = st.number_input("Your answer:", step=1, format="%d", value=None)
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

    # Timer update logic - separate from answer submission
    if time.time() - st.session_state.last_rerun > 0.1:
        st.session_state.last_rerun = time.time()
        st.rerun()
