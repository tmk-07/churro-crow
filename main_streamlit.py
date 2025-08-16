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
from z_padding_function import padding_practice
from z_calc_function import calc_function
from z_driller import driller
from z_check_function import check_function
from z_leaderboard import leaderboard_page
import streamlit as st
from pathlib import Path
import toml
from pathlib import Path
from ztesttimer import render_countdown_video

def start_screen():


    # Centered title
    st.markdown("<h1 style='text-align: center;'>Onsets Tools</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:

        st.markdown("""
    <style>
    /* Make all Streamlit buttons bigger and bold */
    div.stButton > button:first-child {
        font-size: 20px !important;
        font-weight: 700 !important;
        padding: 0.75em 1.5em !important;
    }
    </style>
""", unsafe_allow_html=True)

        if st.button("Solution Checker", use_container_width=True):
            st.session_state.page = "check_function"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Solution Finder", use_container_width=True):
            st.session_state.page = "calc_function"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("Padding Practice", use_container_width=True):
            st.session_state.page = "padding_practice"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("Solution Practice 🚧", use_container_width=True):
            st.session_state.page = "driller"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("Timer", use_container_width=True):
            st.session_state.page = "ztesttimer"
            st.rerun()



if "page" not in st.session_state:
    st.session_state.page = "start"

if st.session_state.page == "start":
    start_screen()
elif st.session_state.page == "calc_function":
    calc_function()
elif st.session_state.page == "check_function":
    check_function()
elif st.session_state.page == "padding_practice":
    padding_practice()
elif st.session_state.page == "driller":
    driller()
elif st.session_state.page == "leaderboard":
    leaderboard_page()
