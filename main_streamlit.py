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


def start_screen():

    # TOML Validation
    st.title("TOML Validator")

    secrets_path = Path(".streamlit/secrets.toml")
    st.write(f"Secrets path: {secrets_path}")

    if secrets_path.exists():
        content = secrets_path.read_text()
        try:
            parsed = toml.loads(content)
            st.success("✅ TOML parsed successfully!")
            
            # Check for required keys
            required_keys = ["SHEET_ID", "gcp_service_account"]
            missing = [key for key in required_keys if key not in parsed]
            
            if missing:
                st.error(f"Missing keys: {', '.join(missing)}")
            else:
                st.success("✅ All required keys present")
                
            st.subheader("Parsed Structure")
            st.json(parsed)
            
        except Exception as e:
            st.error(f"❌ TOML parsing failed: {str(e)}")
            st.subheader("Raw Content")
            st.code(content)
    else:
        st.error("Secrets file not found!")




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