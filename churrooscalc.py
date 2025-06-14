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



def get_color_combinations(colors, operators):
    """Generate all valid color combinations based on operator count"""
    required_colors = len([op for op in operators if op in {'n','u','-','c','='}]) + 1
    
    if len(colors) == required_colors:
        return [tuple(colors)]  # Single combination if exact match
    elif len(colors) > required_colors:
        # Get all possible combinations of required colors
        return list(combinations(colors, required_colors))
    else:
        raise ValueError(
            f"Need at least {required_colors} colors for {len(operators)} operators. "
            f"Only got {len(colors)} colors."
        )

def generate_all_expressions(colors, operators):
    """Generate expressions using exactly all the operators and (operators + 1) colors."""
    num_primes = operators.count("'")
    binary_ops = [op for op in operators if op in {'n', 'u', '-'}]
    clean_ops = binary_ops  # no restriction ops here

    required_color_count = len(clean_ops) + 1
    color_combos = combinations(colors, required_color_count)

    all_expressions = set()

    for color_combo in color_combos:
        for opnd_perm in permutations(color_combo):
            for opr_perm in set(permutations(clean_ops)):
                # Build expression
                expr = []
                for i in range(len(opr_perm)):
                    expr.append(opnd_perm[i])
                    expr.append(opr_perm[i])
                expr.append(opnd_perm[-1])
                expr_str = ''.join(expr)
                all_expressions.add(expr_str)

                # Add prime variants
                if num_primes > 0:
                    for variant in generate_prime_variants(list(expr_str), num_primes):
                        all_expressions.add(variant)

    return all_expressions


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

def new_token(): # creates tokens for new expressions generated
    global token_counter
    token_counter += 1
    return f"T{token_counter}"

def calcExpp(tokens):
    """Safe expression evaluation with empty list handling"""
    if not tokens:
        raise ValueError("Empty expression cannot be evaluated")
    
    ops = ('u','n','-')
    global computed_sets

    # Process primes first
    while "'" in tokens and len(tokens) > 1:
        try:
            i = tokens.index("'")
            if i == 0:
                raise ValueError("Prime cannot be first character")
            result = prime(get_set(tokens[i-1]))
            tok = new_token()
            computed_sets[tok] = result
            tokens[i-1:i+1] = [tok]  # Replace operand and prime
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid prime: {str(e)}")

    # Process binary operators
    while any(op in tokens for op in ops) and len(tokens) >= 3:
        try:
            i = next(idx for idx, tok in enumerate(tokens) if tok in ops)
            if i == 0 or i >= len(tokens)-1:
                raise ValueError("Operator at invalid position")
                
            func = op_map.get(tokens[i])
            result = func(get_set(tokens[i-1]), get_set(tokens[i+1]))
            tok = new_token()
            computed_sets[tok] = result
            tokens[i-1:i+2] = [tok]  # Replace left, op, right
        except StopIteration:
            break
        except Exception as e:
            raise ValueError(f"Operator error: {str(e)}")

    if not tokens:
        raise ValueError("Expression reduced to empty")
    return tokens[0]

def parse(expr):
    """Safe parsing with validation"""
    if not expr or not isinstance(expr, str):
        raise ValueError("Invalid expression input")

    try:
        tokens = tokenize(expr)

        # ✅ Strip out unsupported parentheses
        tokens = [t for t in tokens if t not in ('(', ')')]

        if not tokens:
            raise ValueError("No tokens found in expression")

        final_token = calcExpp(tokens)

        if not final_token:
            raise ValueError("Evaluation returned empty token")

        return final_token

    except Exception as e:
        raise ValueError(f"Failed to parse '{expr}': {str(e)}")

def double_set(expr): # adds the double set cards to universe
    """ adds double setted cards to universe """
    doubled = set_cards(expr,testV=False, doubleWork=True)
    for card in doubled:
        universe[card + ' (2)'] = universe[card] + ['d']
    universeRefresher()

def set_cards(expr, testV=False, doubleWork=False): # returns the set of cards given a solution set
    """ returns the list of cards given an expression """
    myToken = parse(expr)
    mySet = get_set(myToken)
    if testV:
        for card in mySet:
            print(card)
        return f"Solution set has {len(mySet)} cards: {list(mySet)}"
    if doubleWork:
        return mySet
    print(f"Solution set has {len(mySet)} cards: {list(mySet)}")

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

def generate_prime_variants(tokens, num_primes, restriction_ops={'c', '='}):
    """Generate all prime variants while avoiding parentheses around restriction ops"""
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
    
    # Now generate parenthesized expansions, skipping restriction ops
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
            
            # Skip if this would parenthesize a restriction operator
            if any(op in variant[start:end] for op in restriction_ops):
                continue
                
            # Create new variant with expanded parentheses
            new_variant = (
                variant[:start] + 
                '(' + variant[start:end] + ')' + 
                variant[end:]
            )
            expanded_variants.add(new_variant)
    
    return expanded_variants

def minus_parenthesis(tokens, expressions, restriction_ops={'c', '='}):
    """Add parentheses while avoiding wrapping restriction operators"""
    # Always add original
    expressions.add(' '.join(tokens))

    # Look for any '-' with room for 3 elements after it
    for i in range(len(tokens) - 3):
        if tokens[i] == '-':
            # Check if we'd be wrapping any restriction operators
            if any(op in tokens[i+1:i+4] for op in restriction_ops):
                continue
                
            # Wrap tokens[i+1:i+4] in parentheses
            new_tokens = tokens[:i+1] + ['('] + tokens[i+1:i+4] + [')'] + tokens[i+4:]
            expressions.add(' '.join(new_tokens))

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

def quick_solutions(colors, operators, target_size, max_solutions=10, testV=False):
    solutions = []
    seen = set()
    
    for expr in generate_all_expressions(colors, operators):
        try:
            token = parse(expr)
            solution_cards = get_set(token)

            if len(solution_cards) == target_size:
                if testV:
                    solutions.append((expr, solution_cards))  # Raw data only
                else:
                    solutions.append(expr)  # Raw expression only
        except Exception:
            continue
    
    if testV:
        output = []
        if not solutions:
                return "No valid solutions found matching all criteria."
        for i, (expr, cards) in enumerate(solutions, 1):
            output.append(f"Solution {i}:\n")
            output.append(f"    Expression: {expr}\n")
            output.append(f"    Cards: {', '.join(cards)}\n")
        return "\n".join(output)


    return solutions[:max_solutions]  # Limit number of results

def validate_inputs(colors, operators, restriction_ops):
    """
    Validates whether the number of colors is sufficient given the operators and restriction operators.

    Rules:
    - The solution expression must have (#binary_operators + 1) colors.
    - If restriction operators are given, the restriction expression must also have
      (#binary_operators + #restriction_operators + 1) colors.
    - Therefore, total colors required = max(
        #binary_operators + 1,
        #binary_operators + #restriction_operators + 1
      )
    """
    binary_ops = [op for op in operators if op in {'n', 'u', '-'}]
    restriction_ops = [op for op in restriction_ops if op in {'=', 'c'}]

    required_for_solution = len(binary_ops) + 1
    required_for_restriction = len(binary_ops) + len(restriction_ops) + 1 if restriction_ops else 0

    total_required = max(required_for_solution, required_for_restriction)
    color_count = len(colors)

    if len(binary_ops) == 0:
        return False, "You must provide at least one binary operator to generate a solution expression."

    if color_count < total_required:
        return False, f"You provided {color_count} colors, but at least {total_required} are needed for the operators and restrictions."

    return True, "Inputs are valid."

def format_solutions(solutions):
    """Convert raw solutions to pretty output"""
    if not solutions:
        return "No solutions found"
    
    output = []
    for i, (expr, cards) in enumerate(solutions, 1):
        output.append(f"Solution {i}:")
        output.append(f"  Expression: {expr}")
        output.append(f"  Cards: {', '.join(cards)}\n")
    return '\n'.join(output)

def parseR(expr, testV = False, compV = False):
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
        return f"New universe has {len(final_set)} cards: {list(final_set)}"
    if compV:
        return final_set
    print(f"New universe has {len(final_set)} cards: {list(final_set)}")
    return final_set

def generate_all_restrictions(operands, operators, restrictions):
    """Final version with strict operator-prime separation"""
    # Combine operators and validate
    restriction_ops={'c', '='}
    combined_ops = operators + list(restrictions)
    num_primes = combined_ops.count("'")
    clean_ops = [op for op in combined_ops if op != "'"]
    
    expressions = set()
    
    # Generate expressions with larger parentheses groups
    for opnd_perm in permutations(operands):
        for opr_perm in permutations(clean_ops):
            # Build base tokens
            tokens = []
            for i in range(len(opr_perm)):
                tokens.append(opnd_perm[i])
                tokens.append(opr_perm[i])
            tokens.append(opnd_perm[-1])
            
            # Add flat version
            flat_expr = ''.join(tokens)
            expressions.add(flat_expr)
            
            # Generate all possible parenthesized versions
            for start in range(0, len(tokens)-2, 2):
                for end in range(start+2, len(tokens), 2):
                    # Only parenthesize around non-restriction segments
                    segment_ops = {tokens[i] for i in range(start+1, end, 2)}
                    if not segment_ops & restriction_ops:
                        new_tokens = tokens[:]
                        new_tokens[start:end+1] = ['('] + tokens[start:end+1] + [')']
                        new_expr = ''.join(new_tokens)
                        
                        # Verify no restriction ops got enclosed
                        if not has_restricted_parentheses(new_expr, restriction_ops):
                            expressions.add(new_expr)
    
    # Generate prime variants
    all_expressions = set()
    for expr in expressions:
        if num_primes > 0:
            for variant in generate_strict_primes(expr, num_primes, restriction_ops):
                all_expressions.add(variant)
        else:
            all_expressions.add(expr)
    
    return all_expressions

def has_restricted_parentheses(expr, restriction_ops):
    """More efficient parentheses checker"""
    paren_stack = []
    for i, char in enumerate(expr):
        if char == '(':
            paren_stack.append(i)
        elif char == ')':
            if paren_stack:
                start = paren_stack.pop()
                if any(op in expr[start+1:i] for op in restriction_ops):
                    return True
    return False

def generate_strict_primes(expr, primes_left, restriction_ops):
    """Prime generator that allows primes at expression end"""
    if primes_left == 0:
        return {expr}
    
    variants = set()
    # Allow primes after any color or closing )
    for i in [i for i, c in enumerate(expr) if c in mapping or c == ')']:
        new_expr = expr[:i+1] + "'" + expr[i+1:]
        if not has_restricted_parentheses(new_expr, restriction_ops):
            variants.update(generate_strict_primes(new_expr, primes_left-1, restriction_ops))
    
    return variants if variants else {expr}

def comp_restrictions(colors, operators, restrictions, goal):
    """Find valid restrictions that leave >= goal cards"""
    final_restrictions = []
    expressions = generate_all_restrictions(colors, operators, restrictions)
    for expr in expressions:
        try:
            remaining_cards = parseR(expr, compV=True)  # Get cards after restriction
            if len(remaining_cards) >= goal:
                final_restrictions.append((expr, remaining_cards))
        except:
            continue
    return final_restrictions

def comp_solutions(colors, operators, goal, compV=False):
    final_solutions = []
    solution_data = quick_solutions(colors, operators, goal, testV=True)
    
    for item in solution_data:
        try:
            if isinstance(item, tuple):
                expr, cards = item
            else:
                expr = item
                cards = get_set(parse(expr))  # This may now raise ValueError
                
            if len(cards) >= goal:
                final_solutions.append((expr, cards))
        except ValueError as e:
            print(f"Skipping invalid expression: {str(e)}")
            continue
        except Exception as e:
            print(f"Unexpected error with {expr}: {str(e)}")
            continue

    if compV:
        return final_solutions
    # ... rest of function ...


def calc_full_solution(colors, operators, restrictions, goal, max_solutions=5, testV=False):
    """Safe version with comprehensive error handling"""
    try:
        # Input validation
        if not colors or not operators:
            raise ValueError("Colors and operators cannot be empty")
        if not all(c in mapping for c in colors):
            raise ValueError("Invalid color specified")
        
        valid_restrictions = []
        try:
            valid_restrictions = comp_restrictions(colors, operators, restrictions, goal)
        except Exception as e:
            if testV:
                return f"Error generating restrictions: {str(e)}"
            raise

        valid_solutions = []
        try:
            valid_solutions = comp_solutions(colors, operators, goal, compV=True)
        except Exception as e:
            if testV:
                return f"Error generating solutions: {str(e)}"
            raise

        solutions = []
        for res_expr, res_cards in valid_restrictions[:max_solutions*2]:  # Limit for performance
            for sol_expr, sol_cards in valid_solutions[:max_solutions*2]:
                try:
                    common_cards = intersect(res_cards, sol_cards)
                    if len(common_cards) == goal:
                        solutions.append({
                            "restriction": res_expr,
                            "solution": sol_expr,
                            "cards": common_cards
                        })
                        if len(solutions) >= max_solutions:
                            break
                except Exception as e:
                    continue
            if len(solutions) >= max_solutions:
                break

        if testV:
            if not solutions:
                return "No valid solutions found matching all criteria."
            
            output = []
            for i, sol in enumerate(solutions, 1):
                output.append(f"Solution {i}:\n")
                output.append(f"    Restriction: {sol['restriction']}\n")
                output.append(f"    Solution: {sol['solution']}\n")
                output.append(f"    Cards: {', '.join(sol['cards'])}\n")
            return "\n".join(output)

        return solutions

    except Exception as e:
        if testV:
            return f"Calculation failed: {str(e)}"
        raise




    
    


# cProfile.run('quick_solutions(colors,operations,6,10)', sort='cumtime')

# parseR("RnYcBcG")

