import streamlit as st
from PIL import Image
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards, universeRefresher, gen_full_solution
import os
import base64
from io import BytesIO
import uuid

def start_screen():
    # Centered title
    st.markdown("<h1 style='text-align: center;'>Onsets Tools v1.22</h1>", unsafe_allow_html=True)

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

        if st.button("Solution Finder / Checker", use_container_width=True):
            st.session_state.page = "main1"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("Padding Practice 🚧", use_container_width=True):
            st.session_state.page = "main2"
            st.rerun()

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("Solution Practice 🚧", use_container_width=True):
            st.session_state.page = "main3"
            st.rerun()


def main_app1():
    st.title("OS Calculator v5.88")

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
    st.markdown("---")

    st.subheader("What would you like to do?")
    selectMethod = st.selectbox(
        "",['1 - Calculate a solution and/or restriction set','2 - Generate a solution given cubes'],
        label_visibility="collapsed"
    )

    # Initialize variables for different calculation methods
    setName = ""
    restriction = ""
    colorMat = ""
    operationMat = ""
    enterGoal = 0
    solutionsWanted = 1

    # Show appropriate inputs based on selected method
    if selectMethod.startswith('1'):
        # Set expression input
        st.markdown("##### Variations")
        uninter = st.checkbox("u and n Interchangeable 🚧")
        vzinter = st.checkbox("v and z Interchangeable 🚧")
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

    elif selectMethod.startswith('2'):
        # Full solution inputs (not implemented)
        st.markdown("##### Variations")
        uninter = st.checkbox("u and n Interchangeable 🚧")
        vzinter = st.checkbox("v and z Interchangeable 🚧")
        symdif = st.checkbox("Symmetric Difference")
        mops = st.checkbox("Multiple Operations 🚧")
        twosol = st.checkbox("Two Solutions 🚧")
        nonull = st.checkbox("No Null Restrictions 🚧")
        bkwild = st.checkbox("Blank Card Wild 🚧")
        doubleSet = st.text_input("Enter the doubleset, if any. Enter N for none",placeholder="Example: (RnB)'")
        wild_cube = st.text_input("Enter wild cube, if any 🚧", placeholder ="Example: -")
        reqCard = st.text_input("Enter required card, if any",placeholder="Example: BGR")
        forbCard = st.text_input("Enter forbidden card, if any",placeholder="Example: RY")
        
        st.markdown("##### Resource Input")
        
        colorMat = st.text_input(
            "Enter color cubes", 
            placeholder="Example: BVRZGY"
        )
        operationMat = st.text_input(
            "Enter operation cubes", 
            placeholder="Example: nnu'-"
        )
        restrictionMat = st.text_input(
            "Enter restriction cubes (if any)", 
            placeholder="Example: =c"
        )
        enterGoal = st.number_input(
            "What is the goal?", 
            min_value=0, 
            step=1
        )
        solutionsWanted = st.number_input(
            "How many solutions wanted?", 
            min_value=1, 
            step=1,
            value=5
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
            if selectMethod.startswith('1'):
                # Calculate solution set
                output = calc_full_solution(restriction_statement, solution_statement)
                
            elif selectMethod.startswith('2'):
                # Validate inputs for full solution
                valid, message = validate_inputs(
                    list(colorMat), 
                    list(operationMat), 
                    list(restrictionMat)
                )
                
                if not valid:
                    st.error(message)
                elif restrictionMat == "":
                    output = quick_solutions(colorMat,operationMat,enterGoal,solutionsWanted,testV=True,opt3v=True)
                else:
                    # Calculate full solution (not implemented)
                    if reqCard != "N" and reqCard != "":
                        if reqCard not in churrooscalc.universe:
                            output = "Required card not in universe"
                        elif forbCard != "n" and forbCard != "": 
                            output = gen_full_solution(
                                colorMat, 
                                list(operationMat), 
                                list(restrictionMat), 
                                enterGoal, 
                                solutionsWanted, 
                                testV=True,required=reqCard,forbidden=forbCard)
                        else:    
                            output = gen_full_solution(
                                colorMat, 
                                list(operationMat), 
                                list(restrictionMat), 
                                enterGoal, 
                                solutionsWanted, 
                                testV=True,required=reqCard)
                    else:
                        output = gen_full_solution(
                                colorMat, 
                                list(operationMat), 
                                list(restrictionMat), 
                                enterGoal, 
                                solutionsWanted, 
                                testV=True)
                    
            
            # Update status when complete
            status.update(label="✅ Calculations complete!", state="complete")
            
    
            # Display output in expandable section
            # with st.expander("View Results", expanded=True):
            st.markdown(output, unsafe_allow_html=False)

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()

def main_app2():
    st.title("Padding Practice")
    st.markdown("Under construction 🚧")

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()

def main_app3():
    st.title("Solution Finding Practice")
    st.markdown("Under construction 🚧")

    if st.button("back to home"):
        st.session_state.page = "start"
        st.rerun()


if "page" not in st.session_state:
    st.session_state.page = "start"

if st.session_state.page == "start":
    start_screen()
elif st.session_state.page == "main1":
    main_app1()
elif st.session_state.page == "main2":
    main_app2()
elif st.session_state.page == "main3":
    main_app3()