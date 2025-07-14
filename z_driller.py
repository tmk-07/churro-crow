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
    
    # Initialize session state for cell states if not present
    if 'covered' not in st.session_state:
        st.session_state.covered = [[False] * 4 for _ in range(4)]
    
    # Define symbols for the grid
    symbols = [
        ['', '○', '○', '○'],  # First row: empty + 3 circles
        ['✓', '✓', '✓', '✓'],  # Check marks
        ['✓', '✓', '✓', '✓'],
        ['✓', '✓', '✓', '✓']
    ]
    
    # CSS to style the grid
    st.markdown("""
    <style>
        .grid-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 5px;
            margin-bottom: 20px;
            max-width: 500px;
        }
        .grid-cell {
            aspect-ratio: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px;
            border: 1px solid #ccc;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.2s;
        }
        .covered {
            background-color: black !important;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the grid using markdown
    grid_html = '<div class="grid-container">'
    for i in range(4):
        for j in range(4):
            covered_class = "covered" if st.session_state.covered[i][j] else ""
            grid_html += f'<div class="grid-cell {covered_class}">{symbols[i][j]}</div>'
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)
    
    # Create invisible buttons over each cell
    cols = st.columns(4)
    clicked_cell = None
    for i in range(4):
        for j in range(4):
            with cols[j]:
                if st.button(" ", key=f"btn_{i}_{j}", help=f"Toggle cell ({i}, {j})"):
                    clicked_cell = (i, j)
    
    # Handle cell toggle
    if clicked_cell:
        i, j = clicked_cell
        st.session_state.covered[i][j] = not st.session_state.covered[i][j]
        st.rerun()
    
    # Add reset button
    if st.button("Reset All Cells"):
        st.session_state.covered = [[False] * 4 for _ in range(4)]
        st.rerun()

    # Back to home button
    if st.button("Back to Home"):
        st.session_state.page = "start"
        st.rerun()