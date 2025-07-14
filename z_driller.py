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
    st.title("Solution Finding Practice new")
    
    # Initialize session state for cell states
    if 'covered' not in st.session_state:
        st.session_state.covered = [[False]*4 for _ in range(4)]
    
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
            background-color: white;
        }
        .covered {
            background-color: black !important;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create the grid
    st.markdown("Click on any cell to cover/uncover it:")
    with st.container():
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        
        for i in range(4):
            for j in range(4):
                cell_key = f"cell_{i}_{j}"
                cell_class = "grid-cell covered" if st.session_state.covered[i][j] else "grid-cell"
                
                st.markdown(
                    f'<div class="{cell_class}" onclick="updateCell({i},{j})">{symbols[i][j]}</div>',
                    unsafe_allow_html=True
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

    # JavaScript to handle clicks
    st.components.v1.html("""
    <script>
    function updateCell(row, col) {
        Streamlit.setComponentValue({row: row, col: col});
    }
    </script>
    """, height=0)

    # Handle cell clicks
    if st.session_state.get('cell_click'):
        row = st.session_state.cell_click['row']
        col = st.session_state.cell_click['col']
        st.session_state.covered[row][col] = not st.session_state.covered[row][col]
        st.experimental_rerun()

    # Add reset button
    if st.button("Reset All Cells"):
        st.session_state.covered = [[False]*4 for _ in range(4)]
        st.experimental_rerun()

    # Back to home button
    if st.button("Back to Home"):
        st.session_state.page = "start"
        st.rerun()