import streamlit as st
from churrooscalc import double_set, set_cards, parseR, quick_solutions

st.title("OS Calculator v1.5")
  
# Inputs
doubleSet = st.text_input("Enter the doubleset, if any. Enter N for none. Example: (RnB)'")

selectMethod = st.selectbox("What would you like to do?",
                            ['1 - Calculate a solution set',
                             '2 - Calculate a restriction',
                             '3 - Enter cubes and generate a solution',
                             '4 - Find a restriction/solution set (Not implemented)'])

# Defaults for all inputs
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

if st.button("Run calculation"):
    with st.status("Generating solutions...", expanded=True) as status:
        output = []
        if doubleSet != "N":
            double_set(doubleSet)

        if selectMethod.startswith('1'):
            output = set_cards(setName, testV=True)
        elif selectMethod.startswith('2'):
            output = parseR(restriction, testV=True)
        elif selectMethod.startswith('3'):
            output = quick_solutions(colorMat, operationMat, enterGoal, solutionsWanted)
        else:
            output = "Option 4 not implemented yet."
        st.success("done.")
        st.markdown(output, unsafe_allow_html=False)
