from churrooscalc import double_set, find_solutions, set_cards, parseR, quick_solutions
from churroinputs import load_from_user

doubleSet, selectMethod, setName, restriction, colorMat, operationMat, enterGoal, solutionsWanted = load_from_user()

if __name__ == "__main__":
    if doubleSet != "N":
        double_set(doubleSet)
    
    
    
    if selectMethod == '1':
        set_cards(setName, testV = True,streamer=True)
    elif selectMethod == '2':
        parseR(restriction, testV = True)
    elif selectMethod == '3':
        quick_solutions(colorMat, operationMat, enterGoal, solutionsWanted)
        
    
