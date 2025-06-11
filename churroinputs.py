def load_from_user():
    print("First, establish variations\n")
    doubleSet = input("If there is a doubleset, enter it. If none, type N\n")
    
    
    
    selectMethod = input("""\nWhat would you like to do?
                         [1] Calculate a solution set
                         [2] Calculate a restriction
                         [3] Find a solution set
                         [4] Find a restriction/solution set
Enter the number of desired option: """)
    
    setName = None
    restriction = None
    colorMat = None
    operationMat = None
    enterGoal = None
    solutionsWanted = None
    
    if selectMethod == '1':
        setName = input("Enter the set expression. Example: RnG-B\n")
    
    elif selectMethod == '2':
        restriction = input("Enter restriction statement. Example: RnGcB'=G\n")

    elif selectMethod == '3':
        colorMat = input("Enter color cubes. Example: BGYY\n")
        operationMat = input("Enter operation cubes. Example: nnu'-\n")
        enterGoal = int(input("What is the goal?\n"))
        solutionsWanted = int(input("How many solutions wanted?\n"))

    return doubleSet, selectMethod, setName, restriction, colorMat, operationMat, enterGoal, solutionsWanted