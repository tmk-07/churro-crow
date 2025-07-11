import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid
import random
import time

def driller():
    st.title("Solution Finding Practice")
    st.markdown("Under construction 🚧")

    if os.path.exists("onsets_chart.png"):
        st.image("onsets_chart.png")
    else:
        st.error("Image file not found: onsets_chart.png")

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()
