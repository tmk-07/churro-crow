from itertools import permutations, combinations_with_replacement, combinations, product  # Add combinations
import cProfile
from functools import lru_cache
import time

cards = {
    "B": ["b"],
    "R": ["r"],
    "G": ["g"],
    "Y": ["y"],
    "BR": ["b", "r"],
    "BG": ["b", "g"],
    "BY": ["b", "y"],
    "RG": ["r", "g"],
    "RY": ["r", "y"],
    "GY": ["g", "y"],
    "BRG": ["b", "r", "g"],
    "BRY": ["b", "r", "y"],
    "BGY": ["b", "g", "y"],
    "RGY": ["r", "g", "y"],
    "BRGY": ["b", "r", "g", "y"],
    "blank": []
}
universe = cards.copy()


def setUpdate(color): # resets each color set (like B) when a restriction is called
    result = []
    for card in universe:
        if f"{color}".lower() in universe[card]:
            result.append(card)
    return result
def universeRefresher(): # updates the universe and color lists
    global B, R, G, Y
    B = setUpdate("b")
    R = setUpdate("r")
    G = setUpdate("g")
    Y = setUpdate("y")
    mapping['B'] = B
    mapping['R'] = R
    mapping['G'] = G
    mapping['Y'] = Y


# original initialization of color sets
B = []
for card in universe:
    if "b" in universe[card]:
        B.append(card)
R = []
for card in universe:
    if "r" in universe[card]:
        R.append(card)
G = []
for card in universe:
    if "g" in universe[card]:
        G.append(card)
Y = []
for card in universe:
    if "y" in universe[card]:
        Y.append(card)    

colorList = [B,R,G,Y]
mapping = { # finds matching list color when given string
        'R': R,
        'B': B,
        'G': G,
        'Y': Y
    }


# operation and restriction functions    
def intersect(set1, set2):
    return list(set(set1).intersection(set2))

def union(set1, set2):
    return list(set(set1).union(set2))

def minus(set1, set2):
    return list(set(set1).difference(set2))

def symdif(set1, set2):
    return list(set(set1).symmetric_difference(set2))

def prime(set1):
    return list(set(universe.keys()) - set(set1))

def mustc(set1,set2):
    return list(set(union(prime(set1),intersect(set1,set2))))

def equal2(set1,set2):
    return list(set(intersect(mustc(set1,set2),mustc(set2,set1))))

op_map = {
    'n': intersect,
    'u': union,
    '-': minus,
    "'": prime
}
computed_sets = {}
token_counter = 0  
solution_statements = {}



def get_color_combinations(colors, operators): # combinatorics for colors if colors > operators + 1
    """Generates valid color combinations based on operation count."""
    n_ops = len([op for op in operators if op in {'n', 'u', '-', 'c', '='}])  # Count non-prime ops
    required_colors = n_ops + 1
    
    if len(colors) == required_colors:
        return [tuple(colors)]  # Single tuple for consistency
    elif len(colors) > required_colors:
        return list(combinations(colors, required_colors))
    else:
        raise ValueError(f"Need at least {required_colors} colors for {n_ops} operations")

@lru_cache(maxsize=None)
def cached_find_solutions(color_combo, operators_str, target_size):
    """Memoized version of find_solutions."""
    return find_solutions(list(color_combo), list(operators_str), target_size)

def find_solutions_all_combos(all_colors, operators, target_size, max_solutions=10):
    """
    Master solver that handles all color combinations.
    Call this instead of find_solutions when you have extra colors.
    """
    color_combos = get_color_combinations(all_colors, operators)
    all_solutions = []
    
    for combo in color_combos:
        solutions = cached_find_solutions(combo, tuple(operators), target_size)
        all_solutions.extend(solutions)
        if len(all_solutions) >= max_solutions:
            break
    
    # Deduplicate while preserving order
    seen = set()
    unique_solutions = []
    for expr, cards in all_solutions:
        card_key = frozenset(cards)
        if card_key not in seen:
            seen.add(card_key)
            unique_solutions.append((expr, cards))
    
    return unique_solutions[:max_solutions]

def tokenize(expr: str): # reformats input expression into a calculable thing by calcExpp
    """ remove whitespace, then split into individual chars """

    return list(expr.replace(" ", ""))

def get_set(token): # returns the set of cards given an expression
    """ returns the set of cards given an expression """
    if token in mapping:
        return mapping[token]
    elif token in computed_sets:
        return computed_sets[token]
    else:
        print(f"Warning: Unknown token {token}")
        return []  # or raise an error

# def calcExp(tokens): # outdated - doesn't solve parentheses
    ops = ('u','n','-')
    while "'" in tokens:
        i = tokens.index("'")
        if i is None:
            break   
        expHold = prime(get_set(tokens[i-1]))
        tokens[i-1 : i+1] = ['X'] 
        computed_sets['X'] = expHold
    while any(op in tokens for op in ops):
        i = next((idx for idx, tok in enumerate(tokens) if tok in ops), None)
        expHold = op_map.get(tokens[i])(get_set(tokens[i-1]),get_set(tokens[i+1]))
        tokens[i-1 : i+2] = ['X']      # inserts the single token 'X'
        computed_sets['X'] = expHold
    for token in tokens:
        return computed_sets[token]

def new_token(): # creates tokens for new expressions generated
    global token_counter
    token_counter += 1
    return f"T{token_counter}"

def calcExpp(tokens): #algorithm for calculating actual set of cards given an expression
    """"" calculates solution set given an expression. helper for parse function """""
    ops = ('u','n','-')
    global computed_sets

    # Process primes first
    while "'" in tokens:
        i = tokens.index("'")
        result = prime(get_set(tokens[i-1]))
        tok = new_token()
        computed_sets[tok] = result
        # Replace exactly the previous token and the prime symbol
        tokens[i-1 : i+1] = [tok]  

    # Process binary operators
    while any(op in tokens for op in ops):
        i = next(idx for idx, tok in enumerate(tokens) if tok in ops)
        func = op_map.get(tokens[i])
        result = func(get_set(tokens[i-1]), get_set(tokens[i+1]))
        tok = new_token()
        computed_sets[tok] = result
        # Replace exactly the left operand, operator, and right operand
        tokens[i-1 : i+2] = [tok]

    return tokens[0]  # return the single token representing the evaluated set

def parse(expr): # takes solution set input and solves its set
    
    tokens = tokenize(expr)
    
    # Helper to find matching '(' for a given ')'
    def find_matching_open(tokens, close_index):
        count = 0
        for j in range(close_index, -1, -1):
            if tokens[j] == ")":
                count += 1
            elif tokens[j] == "(":
                count -= 1
                if count == 0:
                    return j
        return None  # no matching '(' found

    while ")" in tokens:
        close_idx = tokens.index(")")
        if close_idx + 1 < len(tokens) and tokens[close_idx + 1] == "'":
            # prime applies to parenthesis block
            open_idx = find_matching_open(tokens, close_idx)
            inner_expr = tokens[open_idx + 1 : close_idx]
            result_token = calcExpp(inner_expr)
            result = prime(get_set(result_token))
            tok = new_token()
            computed_sets[tok] = result
            # replace ( ... )' with tok
            tokens[open_idx : close_idx + 2] = [tok]
        else:
            open_idx = find_matching_open(tokens, close_idx)
            inner_expr = tokens[open_idx + 1 : close_idx]
            result_token = calcExpp(inner_expr)
            tokens[open_idx : close_idx + 1] = [result_token]

    # Now evaluate the remaining expression (no parentheses left)
    final_token = calcExpp(tokens)
    return final_token

    # Print results (assuming get_set returns list of cards)
    # final_set = get_set(final_token)
    # for card in final_set:
    #     print(card)
    # print(f"Solution Set Cards: {len(final_set)}")

def double_set(expr): # adds the double set cards to universe
    """ adds double setted cards to universe """
    doubled = set_cards(expr,testV=False)
    for card in doubled:
        universe[card + ' (2)'] = universe[card] + ['d']
    universeRefresher()

def set_cards(expr, testV=False): # returns the set of cards given a solution set
    """ returns the list of cards given an expression """
    myToken = parse(expr)
    mySet = get_set(myToken)
    if testV:
        for card in mySet:
            print(card)
        print(f"Solution Set Cards: {len(mySet)}")
    return f"Solution set has {len(mySet)} cards: {list(mySet)}"

def minus_parenthesis(tokens, expressions): # adds parenthesis around next expression after any minuses
    # Always add original
    expressions.add(' '.join(tokens))

    # Look for any '-' with room for 3 elements after it
    for i in range(len(tokens) - 3):
        if tokens[i] == '-':
            # Wrap tokens[i+1:i+4] in parentheses
            new_tokens = tokens[:i+1] + ['('] + tokens[i+1:i+4] + [')'] + tokens[i+4:]
            expressions.add(' '.join(new_tokens))

def add_primes(tokens, num_primes): # adds primes in all valid positions
    if num_primes == 0:
        return {tuple(tokens)}
    # Candidates are indexes where we can append primes: operands or closing parentheses
    candidate_indices = [i for i, t in enumerate(tokens) if (t.isalpha() or t == ')')]
    variants = set()

    # combinations_with_replacement: primes can stack on same token (e.g., R'')
    for indices_combo in combinations_with_replacement(candidate_indices, num_primes):
        new_tokens = tokens.copy()

        # To avoid index shift while modifying, count how many primes to add per token
        prime_counts = {}
        for idx in indices_combo:
            prime_counts[idx] = prime_counts.get(idx, 0) + 1

        # Insert primes behind tokens, starting from highest index to avoid shifting
        for idx in sorted(prime_counts.keys(), reverse=True):
            new_tokens[idx] = new_tokens[idx] + ("'" * prime_counts[idx])

        variants.add(tuple(new_tokens))

    return variants

def generate_prime_variants(tokens, num_primes): # adds parentheses for each of those prime positions
    """Generate all prime variants with expanding parentheses"""
    base_variants = set()
    candidate_indices = [i for i, t in enumerate(tokens) 
                        if t in mapping or t == ')']
    
    # First generate basic prime placements
    for combo in combinations_with_replacement(candidate_indices, num_primes):
        new_tokens = tokens.copy()
        prime_counts = {}
        
        for idx in combo:
            prime_counts[idx] = prime_counts.get(idx, 0) + 1
        
        for idx in sorted(prime_counts.keys(), reverse=True):
            count = prime_counts[idx]
            new_tokens = new_tokens[:idx+1] + ["'"] * count + new_tokens[idx+1:]
        
        base_variants.add(''.join(new_tokens))
    
    # Now generate parenthesized expansions for each prime
    expanded_variants = set()
    for variant in base_variants:
        expanded_variants.add(variant)  # Keep original
        
        primes_positions = [i for i, c in enumerate(variant) if c == "'"]
        for prime_pos in primes_positions:
            # Find the start of the expression being primed
            start = prime_pos - 1
            while start >= 0:
                if variant[start] == ')':
                    balance = 1
                    start -= 1
                    while balance > 0 and start >= 0:
                        if variant[start] == ')':
                            balance += 1
                        elif variant[start] == '(':
                            balance -= 1
                        start -= 1
                    start += 1
                    break
                elif variant[start] in mapping:
                    break
                start -= 1
            
            # Find the end of the expression
            end = prime_pos + 1
            while end < len(variant):
                if variant[end] == '(':
                    balance = 1
                    end += 1
                    while balance > 0 and end < len(variant):
                        if variant[end] == '(':
                            balance += 1
                        elif variant[end] == ')':
                            balance -= 1
                        end += 1
                    break
                elif end+1 < len(variant) and variant[end+1] == "'":
                    end += 2  # Skip next prime
                elif variant[end] in mapping or variant[end] in {'u','n','-'}:
                    break
                else:
                    end += 1
            
            # Create new variant with expanded parentheses
            new_variant = (
                variant[:start] + 
                '(' + variant[start:end] + ')' + 
                variant[end:]
            )
            expanded_variants.add(new_variant)
    
    return expanded_variants

def generate_all_expressions(operands, operators): # finishes adding possible expressions based on prev 2 functions
    """Generator that yields all possible expressions"""
    num_primes = operators.count("'")
    clean_ops = [op for op in operators if op != "'"]
    
    # Your existing permutation logic
    for opnd_perm in permutations(operands):
        for opr_perm in permutations(clean_ops):
            # Build base expression
            expr = []
            for i in range(len(opr_perm)):
                expr.append(opnd_perm[i])
                expr.append(opr_perm[i])
            expr.append(opnd_perm[-1])
            expr_str = ''.join(expr)
            
            # Generate prime variants (from your code)
            if num_primes > 0:
                for variant in generate_prime_variants(list(expr_str), num_primes):
                    yield variant
            else:
                yield expr_str

def potential_restrictions(restriction_expr, current_universe=None):
    """
    Calculates what the universe WOULD become after a restriction without modifying it
    Args:
        restriction_expr: String like "RcG" or "(RnG)=B"
        current_universe: Optional universe to apply to (defaults to global universe)
    Returns:
        (new_universe_dict, cards_removed)
    """
    if current_universe is None:
        current_universe = universe.copy()
    
    # Split on the restriction operator
    if 'c' in restriction_expr:
        left, right = restriction_expr.split('c', 1)
        op_func = mustc
    elif '=' in restriction_expr:
        left, right = restriction_expr.split('=', 1)
        op_func = equal2
    else:
        raise ValueError("Restriction expr must contain 'c' or '='")
    
    # Evaluate both sides
    left_set = evaluate_expression(left, current_universe)
    right_set = evaluate_expression(right, current_universe)
    
    # Apply the restriction to a copy
    test_universe = current_universe.copy()
    op_func(left_set, right_set)  # This modifies test_universe
    universeRefresher()  # Update color sets
    
    # Return the would-be state
    removed = set(current_universe) - set(test_universe.keys())
    return test_universe, removed

def evaluate_expression(expr, universe_dict):
    """Safely evaluates expressions in alternate universes"""
    global universe
    original_universe = universe
    try:
        universe = universe_dict
        computed_sets.clear()
        global token_counter
        token_counter = 0
        return get_set(parse(expr))
    finally:
        universe = original_universe

def find_solutions(operands, operators,goal): # finds ALL solutions given cubes
    loperands = list(operands)
    loperators = list(operators)
    num_primes = loperators.count("'")
    clean_operators = [op for op in loperators if op != "'"]

    if len(clean_operators) != len(loperands) - 1:
        raise ValueError("Number of non-apostrophe operators must be one fewer than number of operands.")

    expressions = set()
    commutative_ops = {'n', 'u'}
    seen_pairs = set()
    computed_sets.clear()

    # Step 1: Generate base expressions without primes
    for opnd_perm in permutations(loperands):
        for opr_perm in permutations(clean_operators):
            # ... [existing duplicate checking logic] ...
            
            # Build expression
            expr = []
            for i in range(len(opr_perm)):
                expr.append(opnd_perm[i])
                expr.append(opr_perm[i])
            expr.append(opnd_perm[-1])
            minus_parenthesis(expr, expressions)

    # Step 2: Generate all prime variants with parentheses expansions
    all_expressions = set()
    for expr in expressions:
        # Convert to token string (e.g., "R u G - Y" -> "RuG-Y")
        token_str = ''.join(expr.replace(" ", ""))
        
        # Generate all prime variants for this expression
        prime_variants = generate_prime_variants(list(token_str), num_primes)
        all_expressions.update(prime_variants)

    # Step 3: Evaluate all expressions
    solution_statements = {}
    for expr in all_expressions:
        computed_sets.clear()
        global token_counter
        token_counter = 0
        
        try:
            final_token = parse(expr)
            final_set = get_set(final_token)
            solution_statements[expr] = final_set
        except Exception as e:
            print(f"Error evaluating {expr}: {e}")

    # Step 4: Print solutions by size
    
    solutions = [expr for expr, cards in solution_statements.items() 
                if len(cards) == goal]
    solCount = 0
    if solutions:
        print(f"\n--- {goal} CARD SOLUTIONS ({len(solutions)}) ---")
        for expr in sorted(solutions, key=len):
            print(expr)
            solCount+=1
    print(f"{solCount} solutiosn generated")

def quick_solutions(operands, operators, target_size, max_solutions=10):

    """
    Finds solutions using EXACTLY the provided operands (including duplicates)
    without generating additional colors
    """
    # Validate we have enough operands
    required_operands = len([op for op in operators if op in {'n','u','-','c','='}]) + 1
    if len(operands) < required_operands:
        raise ValueError(f"Need at least {required_operands} operands for {operators}")

    solutions = []
    seen = set()
    
    for expr in generate_all_expressions(operands, operators):
        try:
            computed_sets.clear()
            token_counter = 0
            
            final_token = parse(expr)
            solution_cards = get_set(final_token)
            card_key = frozenset(solution_cards)
            
            if len(solution_cards) == target_size and card_key not in seen:
                seen.add(card_key)
                solutions.append((expr, solution_cards))
                
                if len(solutions) >= max_solutions:
                    break
        except:
            continue
    
     # Print results
    print(f"\nFound {len(solutions)} solutions with {target_size} cards")
    output = "Generated solutions:\n\n"
    for i, (expr, cards) in enumerate(solutions, 1):
        output += f"{expr}: {sorted(cards)}  \n"
    return output


def parseR(expr, testV = False):
    """Processes restrictions left-to-right and returns intersection of all intermediate results"""
    
    # Split on operators, preserving order
    parts = []
    current = []
    for char in expr.replace(" ", ""):
        if char in ('c', '='):
            parts.append(''.join(current))
            parts.append(char)
            current = []
        else:
            current.append(char)
    parts.append(''.join(current))
    
    if len(parts) < 3:
        raise ValueError("Need at least two expressions and one operator")
    
    all_results = set(universe.keys())
    # Process each operator-right_expr pair sequentially
    for i in range(1, len(parts), 2):
        operator = parts[i]
        right_expr = parts[i+1]
        left_expr = parts[i-1]
        
        right_set = get_set(parse(right_expr))
        left_set = get_set(parse(left_expr))
        
        if operator == 'c':
            current_set = mustc(left_set, right_set)
        elif operator == '=':
            current_set = equal2(left_set, right_set)
        else:
            raise ValueError(f"Unknown operator: {operator}")
        
        all_results.intersection_update(current_set.copy())  # Store this intermediate result
    # Return intersection of all intermediate results
    final_set = set(all_results)

    if testV:
        print("New universe cards:")
        for i in final_set:
            print(i)
    return f"New universe has {len(final_set)} cards: {list(final_set)}"






# cProfile.run('quick_solutions(colors,operations,6,10)', sort='cumtime')

# parseR("RnYcBcG")

