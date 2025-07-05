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
    questions = [
        ("5 + 7", 12),
        ("9 - 4", 5),
        ("6 × 3", 18),
        ("15 ÷ 3", 5),
        ("8 + 12", 20),
        ("25 - 9", 16),
        ("4 × 7", 28),
        ("36 ÷ 6", 6),
        ("13 + 8", 21),
        ("17 - 5", 12),
        ("9 × 4", 36),
        ("42 ÷ 7", 6),
        ("15 + 6", 21),
        ("23 - 7", 16),
        ("5 × 9", 45),
        ("63 ÷ 9", 7)
    ]

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
    st.title("⏱️ 2-Minute Math Quiz")
    st.write("Test your arithmetic skills! You have 2 minutes to answer as many questions as possible.")

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
