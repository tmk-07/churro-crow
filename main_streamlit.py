import streamlit as st
from PIL import Image
import os
from churrooscalc import double_set, set_cards, parseR, quick_solutions, calc_full_solution, validate_inputs, cards

st.title("OS Calculator v3.1")

# --- Card Selector ---
CARD_ORDER = [
    "blank", "B", "R", "G", "Y",
    "BR", "BG", "BY", "RG", "RY", "GY",
    "BRG", "BRY", "BGY", "RGY", "BRGY"
]

CARD_IMAGE_PATH = "Onsets Cards"  # Folder with 'B.png', 'RGY.png', etc.

def display_card_selector():
    st.subheader("Select the cards you want to include in the universe")

    selected_cards = st.multiselect(
        "Click to remove cards from the universe:",
        CARD_ORDER,
        default=CARD_ORDER,
        format_func=lambda x: x
    )

    cols = st.columns(4)
    for idx, card in enumerate(CARD_ORDER):
        col = cols[idx % 4]
        with col:
            try:
                img_path = os.path.join(CARD_IMAGE_PATH, f"{card}.png")
                img = Image.open(img_path)
                st.image(img, caption=card, use_column_width=True)
            except FileNotFoundError:
                st.markdown(f"`{card}`")

    return selected_cards

# --- Display card selector at the top ---
selected_cards = display_card_selector()
universe = {card: cards[card] for card in selected_cards}

# Override the default universe in churrooscalc
import churrooscalc
churrooscalc.universe = universe

# --- Other Inputs ---
doubleSet = st.text_input("Enter the doubleset, if any. Enter N for none. Example: (RnB)'")

selectMethod = st.selectbox("What would you like to do?",
                            ['1 - Calculate a solution set',
                             '2 - Calculate a restriction',
                             '3 - Enter cubes and generate a solution',
                             '4 - Find a restriction/solution set (Not implemented)'])

setName = ""
restriction = ""
colorMat = ""
operationMat = ""
enterGoal = 0
solutionsWanted = 1

if selectMethod.startswith('1'):
    setName = st.text_input("Enter the set expression. Example: RnG-B or (BnY)'u(R-G)")

elif selectMethod.startswith('2'):
    restriction = st.text_input("Enter restriction statement. Example: BcR or Y=RnGcB'=G")

elif selectMethod.startswith('3'):
    colorMat = st.text_input("Enter color cubes. Example: BGYY")
    operationMat = st.text_input("Enter operation cubes. Example: nnu'-")
    enterGoal = st.number_input("What is the goal?", min_value=0, step=1)
    solutionsWanted = st.number_input("How many solutions wanted?", min_value=1, step=1)

elif selectMethod.startswith('4'):
    colorMat = st.text_input("Enter color cubes. Example: BGYY")
    operationMat = st.text_input("Enter operation cubes. Example: nnu'-")
    restrictionMat = st.text_input("Enter restriction cubes. Example: =c")
    enterGoal = st.number_input("What is the goal?", min_value=0, step=1)
    solutionsWanted = st.number_input("How many solutions wanted?", min_value=1, step=1)

# --- Run Calculation ---
if st.button("Run calculation"):
    with st.status("Generating solutions...", expanded=True) as status:
        output = []
        if doubleSet != "N" and doubleSet != "":
            double_set(doubleSet)

        if selectMethod.startswith('1'):
            output = set_cards(setName, testV=True)
        elif selectMethod.startswith('2'):
            output = parseR(restriction, testV=True)
        elif selectMethod.startswith('3'):
            output = quick_solutions(colorMat, operationMat, enterGoal, solutionsWanted, testV=True)
        elif selectMethod.startswith('4'):
            valid, message = validate_inputs(list(colorMat), list(operationMat), list(restrictionMat))
            if not valid:
                st.error(message)
            else:
                output = calc_full_solution(colorMat, list(operationMat), list(restrictionMat), enterGoal, solutionsWanted, testV=True)
        else:
            output = "Option 4 not implemented yet."
        status.update(label="Calculations complete.", state="complete")
        st.markdown(output, unsafe_allow_html=False)
