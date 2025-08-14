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

        ("B u B'", 'v'),
        ("R' u R", 'v'),
        ("G u G'", 'v'),
        ("Y u Y'", 'v'),

        ("B' n B", 'z'),
        ("R n R'", 'z'),
        ("G' n G", 'z'),
        ("Y n Y'", 'z'),

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
        ("V n Z", 'z'),
        ("Z u V", 'v'),



]

symquestions = [
        ("V n B", 'b'),
        ("V n R", 'r'),
        ("V n G", 'g'),
        ("V n Y", 'y'),

        ("V u B", 'v'),
        ("V u R", 'v'),
        ("V u G", 'v'),
        ("V u Y", 'v'),

        ("B u B'", 'v'),
        ("R' u R", 'v'),
        ("G u G'", 'v'),
        ("Y' u Y'", 'v'),

        ("B' n B", 'z'),
        ("R n R'", 'z'),
        ("G' n G", 'z'),
        ("Y n Y'", 'z'),

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
        ("V n Z", 'z'),
        ("Z u V", 'v'),



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


    def start_quiz():
        st.session_state.quiz_active = True
        st.session_state.end_time = datetime.now() + timedelta(seconds=120)
        st.session_state.score = 0
        st.session_state.current_q = random.choice(questions)
        st.session_state.feedback = None
        st.session_state.question_counter = 0
        st.session_state.last_rerun = time.time()
        st.session_state.last_timer_update = time.time()  # ADD THIS

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
    if not st.session_state.quiz_active:
        st.button("Start Quiz", on_click=start_quiz)
        if st.button("back to home"):
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
        st.write("lmk if im missing any questions")
        if st.button("Play Again"):
            start_quiz()
        if st.button("Back to Home"):
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
