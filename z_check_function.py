import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid
import random
import time

def check_function():

    st.title("OS Solution Checker")

    # Define the order of cards for display
    CARD_ORDER = [
        "BR", "BRY", "BY", "B", 
        "BRG", "BRGY", "BGY", "BG", 
        "RG", "RGY", "GY", "G", 
        "R", "RY", "Y", "blank"
    ]

    # Path to folder containing card images
    CARD_IMAGE_PATH = "Onsets Cards"

    # Enhanced CSS for beautiful toggle buttons and card styling
    st.markdown("""
    <style>
        /* Container for cards */
        .card-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        /* Individual card styling */
        .card-item {
            width: 140px;
            text-align: center;
            transition: all 0.3s ease;
            padding: 0;
            margin: 0;
            box-sizing: border-box;
        }
        
        /* Card image styling */
        .card-image {
            border-radius: 10px;
            border: 4px solid #1f77b4;
            width: 100%;
            height: 140px;
            object-fit: contain;
            background-color: #f0f2f6;
            transition: all 0.3s ease;
            display: block;
            box-sizing: border-box;
        }
        
        /* Card in excluded state */
        .card-excluded .card-image {
            border-color: #ff4b4b !important;
            opacity: 0.7;
        }
        

        
        /* Status indicator */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .included .status-indicator {
            background-color: #1f77b4;
        }
        
        .excluded .status-indicator {
            background-color: #ff4b4b;
        }
        
        /* Summary panel styling */
        .summary-panel {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }
        
    </style>
    """, unsafe_allow_html=True)

    def interactive_card_selector():
        """Interactive card selection interface with beautiful toggle buttons"""
        st.subheader("Toggle cards to include/exclude from the universe")
        
        # Initialize session state for card states
        if 'card_states' not in st.session_state:
            st.session_state.card_states = {card: True for card in CARD_ORDER}
        
        # Create a container for the cards
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # Create 4 columns for the grid layout
        cols = st.columns(4)
        
        # Display cards in grid
        for idx, card in enumerate(CARD_ORDER):
            is_included = st.session_state.card_states[card]
            card_class = "card-item" if is_included else "card-item excluded"
            
            # Determine which column to use
            col = cols[idx % 4]
            
            with col:
                try:
                    img_path = os.path.join(CARD_IMAGE_PATH, f"{card}.png")
                    img = Image.open(img_path)
                    
                    # Convert image to base64
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_b64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Display card image
                    st.markdown(
                        f"""
                        <div class="{card_class}">
                            <img src="data:image/png;base64,{img_b64}" class="card-image">
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                except FileNotFoundError:
                    # Fallback for missing images
                    st.markdown(
                        f"""
                        <div class="{card_class}">
                            <div style="height:140px; display:flex; align-items:center; justify-content:center; background:#f0f2f6; border-radius:10px; border:2px dashed #ccc;">
                                <strong>{card}</strong>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Create a hidden button to handle state changes
                if st.button(f"   {card}   ", key=f"btn_{card}"):
                    st.session_state.card_states[card] = not st.session_state.card_states[card]
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Summary panel
        included_count = sum(st.session_state.card_states.values())
        excluded_count = len(CARD_ORDER) - included_count
        
        # Get included/excluded card lists
        included_cards = [card for card in CARD_ORDER if st.session_state.card_states[card]]
        excluded_cards = [card for card in CARD_ORDER if not st.session_state.card_states[card]]
        
        # Create summary panel
        with st.container():
            st.markdown('<div class="summary-panel">', unsafe_allow_html=True)
            st.markdown("### Selection Summary")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**<span class='included'><span class='status-indicator'></span> Included Cards ({included_count})</span>**", 
                            unsafe_allow_html=True)
                st.caption(", ".join(included_cards) if included_cards else "None")
            
            with col2:
                st.markdown(f"**<span class='excluded'><span class='status-indicator'></span> Excluded Cards ({excluded_count})</span>**", 
                            unsafe_allow_html=True)
                st.caption(", ".join(excluded_cards) if excluded_cards else "None")
            
            st.markdown('</div>', unsafe_allow_html=True)

        return included_cards



    # --- Main Application Flow ---

    # Display card selector and get selected cards
    selected_cards = interactive_card_selector()

    # Create universe dictionary from selected cards
    universe = {card: cards[card] for card in selected_cards}

    # Override default universe in churrooscalc module
    import churrooscalc
    churrooscalc.universe = universe
    # Refresh universe dependencies
    universeRefresher()

    # --- User Input Section ---

    # Double set input (optional)
    # st.markdown("---")

  

    # Initialize variables for different calculation methods
    setName = ""
    restriction = ""
    colorMat = ""
    operationMat = ""
    enterGoal = 0
    solutionsWanted = 1


    st.markdown("##### Variations")
    # uninter = st.checkbox("u and n Interchangeable 🚧")
    # vzinter = st.checkbox("v and z Interchangeable 🚧")
    symdif = st.checkbox("Symmetric Difference")
    doubleSet = st.text_input(
        "Enter the doubleset, if any. Enter N for none",
        placeholder="Example: (RnB)'"
    )
    st.markdown("##### Expression Input")
    restriction_statement = st.text_input(
        "Enter the restriction statement (if any)", 
        placeholder="Example: BuG'cR=(YnG)=GuR'"
    )
    solution_statement = st.text_input(
        "Enter the solution expression (if any)",
        placeholder="Example: (R-Y)'u(B'nY)"
    )

    

    # --- Calculation Execution ---
    st.markdown("---")
    if st.button("Run calculation", use_container_width=True, type="primary"):
        # Display status during calculation
        with st.status("🚀 Generating solutions...", expanded=True) as status:
            output = []
            
            # Process doubleset if provided
            if doubleSet != "N" and doubleSet != "":
                double_set(doubleSet)

            if symdif:
                churrooscalc.op_map['-'] = churrooscalc.symdif
            else:
                churrooscalc.op_map['-'] = churrooscalc.minus


            # Execute selected calculation method
            
                # Calculate solution set
            output = calc_full_solution(restriction_statement, solution_statement)
                
            
            
            # Update status when complete
            status.update(label="✅ Calculations complete!", state="complete")
            

            # Display output in expandable section
            # with st.expander("View Results", expanded=True):
            st.markdown(output, unsafe_allow_html=False)

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()

