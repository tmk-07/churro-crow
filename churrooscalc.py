from itertools import permutations, combinations_with_replacement, combinations, product
import cProfile
from functools import lru_cache
import time
from collections import Counter



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


def setUpdate(color):
    result = []
    for card in universe:
        if f"{color}".lower() in universe[card]:
            result.append(card)
    return result

def universeRefresher():
    global B, R, G, Y, V, Z
    B = setUpdate("b")
    R = setUpdate("r")
    G = setUpdate("g")
    Y = setUpdate("y")
    V = list(universe.keys())
    Z = []
    mapping['B'] = B
    mapping['R'] = R
    mapping['G'] = G
    mapping['Y'] = Y
    mapping['V'] = V
    mapping['Z'] = Z


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
V = []
for card in universe:
    V.append(card)
Z = []


colorList = [B, R, G, Y]
mapping = {
    'R': R,
    'B': B,
    'G': G,
    'Y': Y,
    'V': V,
    'Z': Z
}


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

def mustc(set1, set2):
    return list(set(union(prime(set1), intersect(set1, set2))))

def equal2(set1, set2):
    return list(set(intersect(mustc(set1, set2), mustc(set2, set1))))

op_map = {
    'n': intersect,
    'u': union,
    '-': minus,
    "'": prime
}
computed_sets = {}
token_counter = 0
solution_statements = {}


COLOR_CUBES = set("BRGYVZ")
SOLUTION_OP_CUBES = set("nu-'")
RESTRICTION_CUBES = set("c=")
ALL_CUBES = COLOR_CUBES | SOLUTION_OP_CUBES | RESTRICTION_CUBES
BOTH_EXPR_ALLOWED = COLOR_CUBES | SOLUTION_OP_CUBES


def parse_cube_inventory(cube_string):
    cube_string = cube_string.replace(" ", "")
    counts = Counter(cube_string)
    invalid = [ch for ch in counts if ch not in ALL_CUBES]
    if invalid:
        raise ValueError(f"Invalid cube symbols: {invalid}")
    return counts

def expand_counter(counter, allowed):
    out = []
    for ch, n in counter.items():
        if ch in allowed:
            out.extend([ch] * n)
    return out

def expression_cube_usage(expr):
    return Counter(ch for ch in expr if ch in ALL_CUBES)

def covers_required(used, required):
    return all(used[sym] >= count for sym, count in required.items())

def within_available(used, available):
    return all(used[sym] <= available[sym] for sym in used)

def required_feasible_in_both(required_inv, available_inv):
    return all(available_inv[sym] >= 2 * count for sym, count in required_inv.items())

def validate_required_cubes_for_both(required_inv):
    bad = [sym for sym in required_inv if sym not in BOTH_EXPR_ALLOWED]
    if bad:
        raise ValueError(
            f"These required cubes cannot appear in both expressions: {bad}. "
            f"Restriction-only cubes like c and = cannot be required."
        )

def has_restriction_cubes(counter):
    return sum(counter[sym] for sym in RESTRICTION_CUBES) > 0

def required_needs_restriction(required_inv):
    return any(required_inv[sym] > 0 for sym in RESTRICTION_CUBES)

def strip_restriction_cubes(counter):
    return Counter({sym: count for sym, count in counter.items() if sym not in RESTRICTION_CUBES})

def counter_total(counter, symbols):
    return sum(counter[sym] for sym in symbols)

def min_colors_needed_for_solution(counter):
    return counter_total(counter, {'n', 'u', '-'}) + 1

def min_colors_needed_for_restriction(counter):
    return counter_total(counter, {'n', 'u', '-', 'c', '='}) + 1

def minimum_pair_required_usage(required_inv):
    restriction_required = required_inv.copy()
    solution_required = strip_restriction_cubes(required_inv)
    return restriction_required + solution_required


def get_color_combinations(colors, operators):
    required_colors = len([op for op in operators if op in {'n', 'u', '-', 'c', '='}]) + 1

    if len(colors) == required_colors:
        return [tuple(colors)]
    elif len(colors) > required_colors:
        return list(combinations(colors, required_colors))
    else:
        raise ValueError(
            f"Need at least {required_colors} colors for {len(operators)} operators. "
            f"Only got {len(colors)} colors."
        )

def generate_all_expressions(colors, operators):
    num_primes = operators.count("'")
    binary_ops = [op for op in operators if op in {'n', 'u', '-'}]
    clean_ops = binary_ops

    required_color_count = len(clean_ops) + 1
    color_combos = combinations(colors, required_color_count)

    all_expressions = set()

    for color_combo in color_combos:
        for opnd_perm in permutations(color_combo):
            for opr_perm in set(permutations(clean_ops)):
                expr = []
                for i in range(len(opr_perm)):
                    expr.append(opnd_perm[i])
                    expr.append(opr_perm[i])
                expr.append(opnd_perm[-1])
                expr_str = ''.join(expr)
                all_expressions.add(expr_str)

                if num_primes > 0:
                    for variant in generate_prime_variants(list(expr_str), num_primes):
                        all_expressions.add(variant)
                    all_expressions.discard(expr_str)
    return all_expressions


@lru_cache(maxsize=None)
def cached_find_solutions(color_combo, operators_str, target_size):
    return find_solutions(list(color_combo), list(operators_str), target_size)

def find_solutions_all_combos(all_colors, operators, target_size, max_solutions=10):
    color_combos = get_color_combinations(all_colors, operators)
    all_solutions = []

    for combo in color_combos:
        solutions = cached_find_solutions(combo, tuple(operators), target_size)
        all_solutions.extend(solutions)
        if len(all_solutions) >= max_solutions:
            break

    seen = set()
    unique_solutions = []
    for expr, cards in all_solutions:
        card_key = frozenset(cards)
        if card_key not in seen:
            seen.add(card_key)
            unique_solutions.append((expr, cards))

    return unique_solutions[:max_solutions]

def tokenize(expr: str):
    return list(expr.replace(" ", ""))

def get_set(token):
    if token in mapping:
        return mapping[token]
    elif token in computed_sets:
        return computed_sets[token]
    else:
        print(f"Warning: Unknown token {token}")
        return []

def new_token():
    global token_counter
    token_counter += 1
    return f"T{token_counter}"

def calcExpp(tokens):
    if not tokens:
        raise ValueError("Empty expression cannot be evaluated")

    ops = ('u', 'n', '-')
    global computed_sets

    while "'" in tokens and len(tokens) > 1:
        try:
            i = tokens.index("'")
            if i == 0:
                raise ValueError("Prime cannot be first character")
            result = prime(get_set(tokens[i - 1]))
            tok = new_token()
            computed_sets[tok] = result
            tokens[i - 1:i + 1] = [tok]
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid prime: {str(e)}")

    while any(op in tokens for op in ops) and len(tokens) >= 3:
        try:
            i = next(idx for idx, tok in enumerate(tokens) if tok in ops)
            if i == 0 or i >= len(tokens) - 1:
                raise ValueError("Operator at invalid position")

            func = op_map.get(tokens[i])
            result = func(get_set(tokens[i - 1]), get_set(tokens[i + 1]))
            tok = new_token()
            computed_sets[tok] = result
            tokens[i - 1:i + 2] = [tok]
        except StopIteration:
            break
        except Exception as e:
            raise ValueError(f"Operator error: {str(e)}")

    if not tokens:
        raise ValueError("Expression reduced to empty")
    return tokens[0]


def parse(expr):
    if not expr or not isinstance(expr, str):
        raise ValueError("Invalid expression input")

    try:
        tokens = tokenize(expr)

        def find_matching_open(tokens, close_index):
            count = 0
            for j in range(close_index, -1, -1):
                if tokens[j] == ")":
                    count += 1
                elif tokens[j] == "(":
                    count -= 1
                    if count == 0:
                        return j
            return None

        while ")" in tokens:
            close_idx = tokens.index(")")
            if close_idx + 1 < len(tokens) and tokens[close_idx + 1] == "'":
                open_idx = find_matching_open(tokens, close_idx)
                inner_expr = tokens[open_idx + 1: close_idx]
                result_token = calcExpp(inner_expr)
                result = prime(get_set(result_token))
                tok = new_token()
                computed_sets[tok] = result
                tokens[open_idx: close_idx + 2] = [tok]
            else:
                open_idx = find_matching_open(tokens, close_idx)
                inner_expr = tokens[open_idx + 1: close_idx]
                result_token = calcExpp(inner_expr)
                tokens[open_idx: close_idx + 1] = [result_token]

        final_token = calcExpp(tokens)
        return final_token

    except Exception as e:
        raise ValueError(f"Failed to parse '{expr}': {str(e)}")


def double_set(expr):
    doubled = set_cards(expr, testV=False, doubleWork=True)
    for card in doubled:
        universe[card + ' (2)'] = universe[card] + ['d']
    universeRefresher()

def set_cards(expr, testV=False, doubleWork=False, calcV=False):
    myToken = parse(expr)
    mySet = get_set(myToken)
    if testV:
        for card in mySet:
            print(card)
        return f"Solution set has {len(mySet)} cards: {list(mySet)}"
    if doubleWork:
        return mySet
    if calcV:
        return mySet
    print(f"Solution set has {len(mySet)} cards: {list(mySet)}")
    return mySet


def add_primes(tokens, num_primes):
    if num_primes == 0:
        return {tuple(tokens)}
    candidate_indices = [i for i, t in enumerate(tokens) if (t.isalpha() or t == ')')]
    variants = set()

    for indices_combo in combinations_with_replacement(candidate_indices, num_primes):
        new_tokens = tokens.copy()

        prime_counts = {}
        for idx in indices_combo:
            prime_counts[idx] = prime_counts.get(idx, 0) + 1

        for idx in sorted(prime_counts.keys(), reverse=True):
            new_tokens[idx] = new_tokens[idx] + ("'" * prime_counts[idx])

        variants.add(tuple(new_tokens))

    return variants

def generate_prime_variants(tokens, num_primes, restriction_ops={'c', '='}):
    base_variants = set()
    candidate_indices = [i for i, t in enumerate(tokens)
                        if t in mapping or t == ')']

    for combo in combinations_with_replacement(candidate_indices, num_primes):
        new_tokens = tokens.copy()
        prime_counts = {}

        for idx in combo:
            prime_counts[idx] = prime_counts.get(idx, 0) + 1

        for idx in sorted(prime_counts.keys(), reverse=True):
            count = prime_counts[idx]
            new_tokens = new_tokens[:idx + 1] + ["'"] * count + new_tokens[idx + 1:]

        base_variants.add(''.join(new_tokens))

    expanded_variants = set()
    for variant in base_variants:
        expanded_variants.add(variant)

        primes_positions = [i for i, c in enumerate(variant) if c == "'"]
        for prime_pos in primes_positions:
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
                elif end + 1 < len(variant) and variant[end + 1] == "'":
                    end += 2
                elif variant[end] in mapping or variant[end] in {'u', 'n', '-'}:
                    break
                else:
                    end += 1

            if any(op in variant[start:end] for op in restriction_ops):
                continue

            new_variant = (
                variant[:start] +
                '(' + variant[start:end] + ')' +
                variant[end:]
            )
            expanded_variants.add(new_variant)
    return expanded_variants

def minus_parenthesis(tokens, expressions, restriction_ops={'c', '='}):
    expressions.add(' '.join(tokens))

    for i in range(len(tokens) - 3):
        if tokens[i] == '-':
            if any(op in tokens[i + 1:i + 4] for op in restriction_ops):
                continue

            new_tokens = tokens[:i + 1] + ['('] + tokens[i + 1:i + 4] + [')'] + tokens[i + 4:]
            expressions.add(' '.join(new_tokens))

def potential_restrictions(restriction_expr, current_universe=None):
    if current_universe is None:
        current_universe = universe.copy()

    if 'c' in restriction_expr:
        left, right = restriction_expr.split('c', 1)
        op_func = mustc
    elif '=' in restriction_expr:
        left, right = restriction_expr.split('=', 1)
        op_func = equal2
    else:
        raise ValueError("Restriction expr must contain 'c' or '='")

    left_set = evaluate_expression(left, current_universe)
    right_set = evaluate_expression(right, current_universe)

    test_universe = current_universe.copy()
    op_func(left_set, right_set)
    universeRefresher()

    removed = set(current_universe) - set(test_universe.keys())
    return test_universe, removed

def evaluate_expression(expr, universe_dict):
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


def find_solutions(operands, operators, goal):
    loperands = list(operands)
    loperators = list(operators)
    num_primes = loperators.count("'")
    clean_operators = [op for op in loperators if op != "'"]

    if len(clean_operators) != len(loperands) - 1:
        raise ValueError("Number of non-apostrophe operators must be one fewer than number of operands.")

    expressions = set()
    computed_sets.clear()

    for opnd_perm in permutations(loperands):
        for opr_perm in permutations(clean_operators):
            expr = []
            for i in range(len(opr_perm)):
                expr.append(opnd_perm[i])
                expr.append(opr_perm[i])
            expr.append(opnd_perm[-1])
            minus_parenthesis(expr, expressions)

    all_expressions = set()
    for expr in expressions:
        token_str = ''.join(expr.replace(" ", ""))
        prime_variants = generate_prime_variants(list(token_str), num_primes)
        all_expressions.update(prime_variants)
        all_expressions.discard(token_str)

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

    solutions = [expr for expr, cards in solution_statements.items()
                if len(cards) == goal]
    solCount = 0
    if solutions:
        print(f"\n--- {goal} CARD SOLUTIONS ({len(solutions)}) ---")
        for expr in sorted(solutions, key=len):
            print(expr)
            solCount += 1
    print(f"{solCount} solutiosn generated")


def quick_solutions(colors, operators, target_size, max_solutions=10, testV=False, compV=False, opt3v=False, requ="", forbi=""):
    solutions = []

    for expr in generate_all_expressions(colors, operators):
        try:
            token = parse(expr)
            solution_cards = get_set(token)
            if requ != "" and requ in solution_cards:
                if forbi not in solution_cards:
                    if testV and not opt3v:
                        if len(solution_cards) >= target_size:
                            solutions.append((expr, solution_cards))
                    elif opt3v:
                        if len(solution_cards) == target_size:
                            solutions.append((expr, solution_cards))
                    else:
                        solutions.append(expr)
            elif requ == "":
                if forbi not in solution_cards:
                    if testV and not opt3v:
                        if len(solution_cards) >= target_size:
                            solutions.append((expr, solution_cards))
                    elif opt3v:
                        if len(solution_cards) == target_size:
                            solutions.append((expr, solution_cards))
                    else:
                        solutions.append(expr)
        except Exception:
            continue

    if testV:
        output = []
        if not solutions:
            return "No valid solutions found matching all criteria 😭🥀"
        for i, (expr, cards) in enumerate(solutions, 1):
            output.append(f"Solution {i}:\n")
            output.append(f"    Expression: {expr}\n")
            output.append(f"    Cards: {', '.join(cards)}\n")
        return "\n".join(output)
    if compV:
        return solutions

    return solutions[:max_solutions]


def validate_inputs(colors, operators, restriction_ops):
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


def validate_inventory_inputs(required_cubes, permitted_cubes):
    try:
        required_inv = parse_cube_inventory(required_cubes)
        permitted_inv = parse_cube_inventory(permitted_cubes)
        available_inv = required_inv + permitted_inv

        total_binary_ops_available = counter_total(available_inv, {'n', 'u', '-'})
        total_colors_available = counter_total(available_inv, COLOR_CUBES)

        if total_binary_ops_available == 0:
            return False, "You must provide at least one binary operator."

        if required_needs_restriction(required_inv):
            solution_required = strip_restriction_cubes(required_inv)
            restriction_required = required_inv.copy()

            min_color_solution = min_colors_needed_for_solution(solution_required)
            min_color_restriction = min_colors_needed_for_restriction(restriction_required)
            min_total_colors_needed = max(min_color_solution, min_color_restriction)

            if total_colors_available < min_total_colors_needed:
                return False, f"You provided {total_colors_available} colors, but at least {min_total_colors_needed} are needed."

        else:
            solution_required = required_inv.copy()
            min_colors_needed = min_colors_needed_for_solution(solution_required)

            if total_colors_available < min_colors_needed:
                return False, f"You provided {total_colors_available} colors, but at least {min_colors_needed} are needed."

            if not within_available(solution_required, available_inv):
                return False, "Not enough total cubes to build the required solution expression."

        return True, "Inputs are valid."

    except Exception as e:
        return False, str(e)

def format_solutions(solutions):
    if not solutions:
        return "No solutions found 🥀"

    output = []
    for i, (expr, cards) in enumerate(solutions, 1):
        output.append(f"Solution {i}:")
        output.append(f"  Expression: {expr}")
        output.append(f"  Cards: {', '.join(cards)}\n")
    return '\n'.join(output)


def parseR(expr, testV=False, compV=False, calcV=False, requ=""):
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

    for i in range(1, len(parts), 2):
        operator = parts[i]
        right_expr = parts[i + 1]
        left_expr = parts[i - 1]
        right_set = get_set(parse(right_expr))
        left_set = get_set(parse(left_expr))

        if operator == 'c':
            current_set = mustc(left_set, right_set)
        elif operator == '=':
            current_set = equal2(left_set, right_set)
        else:
            raise ValueError(f"Unknown operator: {operator}")
        all_results.intersection_update(current_set.copy())

    final_set = set(all_results)

    if testV:
        return f"New universe has {len(final_set)} cards: {list(final_set)}"
    if compV:
        return final_set
    if calcV:
        return final_set
    return final_set


def generate_all_restrictions(operands, operators, restrictions):
    restriction_ops = {'c', '='}
    combined_ops = operators + list(restrictions)
    num_primes = combined_ops.count("'")
    clean_ops = [op for op in combined_ops if op != "'"]

    expressions = set()

    for opnd_perm in permutations(operands):
        for opr_perm in permutations(clean_ops):
            tokens = []
            for i in range(len(opr_perm)):
                tokens.append(opnd_perm[i])
                tokens.append(opr_perm[i])
            tokens.append(opnd_perm[-1])

            flat_expr = ''.join(tokens)
            expressions.add(flat_expr)

            for start in range(0, len(tokens) - 2, 2):
                for end in range(start + 2, len(tokens), 2):
                    segment_ops = {tokens[i] for i in range(start + 1, end, 2)}
                    if not segment_ops & restriction_ops:
                        new_tokens = tokens[:]
                        new_tokens[start:end + 1] = ['('] + tokens[start:end + 1] + [')']
                        new_expr = ''.join(new_tokens)

                        if not has_restricted_parentheses(new_expr, restriction_ops):
                            expressions.add(new_expr)

    all_expressions = set()
    for expr in expressions:
        if num_primes > 0:
            for variant in generate_strict_primes(expr, num_primes, restriction_ops):
                all_expressions.add(variant)
        else:
            all_expressions.add(expr)

    return all_expressions

def has_restricted_parentheses(expr, restriction_ops):
    paren_stack = []
    for i, char in enumerate(expr):
        if char == '(':
            paren_stack.append(i)
        elif char == ')':
            if paren_stack:
                start = paren_stack.pop()
                if any(op in expr[start + 1:i] for op in restriction_ops):
                    return True
    return False

def generate_strict_primes(expr, primes_left, restriction_ops):
    if primes_left == 0:
        return {expr}

    variants = set()
    for i in [i for i, c in enumerate(expr) if c in mapping or c == ')']:
        new_expr = expr[:i + 1] + "'" + expr[i + 1:]
        if not has_restricted_parentheses(new_expr, restriction_ops):
            variants.update(generate_strict_primes(new_expr, primes_left - 1, restriction_ops))

    return variants if variants else {expr}


def comp_restrictions(colors, operators, restrictions, goal, req=""):
    final_restrictions = []
    expressions = generate_all_restrictions(colors, operators, restrictions)
    for expr in expressions:
        try:
            remaining_cards = parseR(expr, compV=True)
            if req != "" and req in remaining_cards:
                if len(remaining_cards) >= goal:
                    final_restrictions.append((expr, remaining_cards))
            elif req == "":
                if len(remaining_cards) >= goal:
                    final_restrictions.append((expr, remaining_cards))
        except:
            continue
    return final_restrictions

def comp_solutions(colors, operators, goal, compV=False, req="", forb=""):
    final_solutions = []
    solution_data = quick_solutions(colors, operators, goal, compV=True, requ=req, forbi=forb)

    for item in solution_data:
        try:
            if isinstance(item, tuple):
                expr, cards = item
            else:
                expr = item
                cards = get_set(parse(expr))
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
    return final_solutions


def iter_inventory_variants(required_base, permitted_inv, allowed_symbols, expr_type):
    """
    Build exact per-expression inventories:
    required_base + any subset of permitted cubes allowed for this expression type.
    """
    permitted_allowed = Counter({
        sym: permitted_inv[sym]
        for sym in permitted_inv
        if sym in allowed_symbols and permitted_inv[sym] > 0
    })

    symbols = sorted(permitted_allowed.keys())

    def recurse(i, extras):
        if i == len(symbols):
            inv = required_base + extras

            binary_ops = counter_total(inv, {'n', 'u', '-'})
            color_count = counter_total(inv, COLOR_CUBES)

            if binary_ops < 1:
                return

            if expr_type == "solution":
                if color_count < binary_ops + 1:
                    return
            elif expr_type == "restriction":
                restriction_count = counter_total(inv, RESTRICTION_CUBES)
                clean_ops = counter_total(inv, {'n', 'u', '-', 'c', '='})
                if restriction_count < 1:
                    return
                if color_count < clean_ops + 1:
                    return
            else:
                raise ValueError("expr_type must be 'solution' or 'restriction'")

            yield inv
            return

        sym = symbols[i]
        max_count = permitted_allowed[sym]
        for count in range(max_count + 1):
            new_extras = extras.copy()
            if count > 0:
                new_extras[sym] = count
            yield from recurse(i + 1, new_extras)

    yield from recurse(0, Counter())


def collect_solution_candidates(required_base, permitted_inv, target_size, req_card="", forb_card=""):
    """
    required_base = cubes that MUST appear in the solution expression
    permitted_inv = cubes that MAY be added to the solution expression
    """
    seen = {}
    allowed_symbols = COLOR_CUBES | SOLUTION_OP_CUBES

    for inv in iter_inventory_variants(required_base, permitted_inv, allowed_symbols, "solution"):
        colors = expand_counter(inv, COLOR_CUBES)
        operators = expand_counter(inv, SOLUTION_OP_CUBES)

        raw = quick_solutions(
            colors,
            operators,
            target_size,
            compV=True,
            requ=req_card,
            forbi=forb_card
        )

        for item in raw:
            try:
                if isinstance(item, tuple):
                    expr, cards = item
                else:
                    expr = item
                    cards = get_set(parse(expr))

                usage = expression_cube_usage(expr)

                if not covers_required(usage, required_base):
                    continue
                if not within_available(usage, inv):
                    continue
                if len(cards) != target_size:
                    continue

                seen[expr] = {
                    "expr": expr,
                    "cards": cards,
                    "usage": usage
                }
            except Exception:
                continue

    results = list(seen.values())
    results.sort(key=lambda x: (sum(x["usage"].values()), len(x["expr"]), x["expr"]))
    return results


def collect_restriction_candidates(required_base, permitted_inv, goal, req_card=""):
    """
    required_base = cubes that MUST appear in the restriction expression
    permitted_inv = cubes that MAY be added to the restriction expression
    """
    seen = {}
    allowed_symbols = COLOR_CUBES | SOLUTION_OP_CUBES | RESTRICTION_CUBES

    for inv in iter_inventory_variants(required_base, permitted_inv, allowed_symbols, "restriction"):
        colors = expand_counter(inv, COLOR_CUBES)
        operators = expand_counter(inv, SOLUTION_OP_CUBES)
        restrictions = expand_counter(inv, RESTRICTION_CUBES)

        expressions = generate_all_restrictions(colors, operators, restrictions)

        for expr in expressions:
            try:
                usage = expression_cube_usage(expr)

                if not covers_required(usage, required_base):
                    continue
                if not within_available(usage, inv):
                    continue

                remaining_cards = parseR(expr, compV=True)

                if req_card != "" and req_card not in remaining_cards:
                    continue
                if len(remaining_cards) < goal:
                    continue

                seen[expr] = {
                    "expr": expr,
                    "cards": remaining_cards,
                    "usage": usage
                }
            except Exception:
                continue

    results = list(seen.values())
    results.sort(key=lambda x: (sum(x["usage"].values()), len(x["expr"]), x["expr"]))
    return results


def format_inventory_results(results):
    if not results:
        return "No valid solutions found matching all criteria 😭🥀"

    output = []
    for i, sol in enumerate(results, 1):
        output.append(f"Solution {i}:\n")
        if "restriction" in sol:
            output.append(f"    Restriction: {sol['restriction']}\n")
        output.append(f"    Solution: {sol['solution']}\n")
        output.append(f"    Cards: {', '.join(sol['cards'])}\n")
    return "\n".join(output)


def comp_solutions_from_inventory(available_inv, required_inv, goal, req="", forb=""):
    """
    Compatibility wrapper. This now treats available_inv as the optional add-on pool
    and required_inv as the mandatory per-solution requirement.
    """
    return collect_solution_candidates(
        required_base=required_inv,
        permitted_inv=available_inv,
        target_size=goal,
        req_card=req,
        forb_card=forb
    )


def comp_restrictions_from_inventory(available_inv, required_inv, goal, req=""):
    """
    Compatibility wrapper. This now treats available_inv as the optional add-on pool
    and required_inv as the mandatory per-restriction requirement.
    """
    return collect_restriction_candidates(
        required_base=required_inv,
        permitted_inv=available_inv,
        goal=goal,
        req_card=req
    )


def quick_solutions_inventory(required_cubes, permitted_cubes, target_size, max_solutions=10, testV=False, compV=False, req_card="", forb_card=""):
    required_inv = parse_cube_inventory(required_cubes)
    permitted_inv = parse_cube_inventory(permitted_cubes)

    results = collect_solution_candidates(
        required_base=required_inv,
        permitted_inv=permitted_inv,
        target_size=target_size,
        req_card=req_card,
        forb_card=forb_card
    )

    formatted = [
        {
            "solution": item["expr"],
            "cards": item["cards"]
        }
        for item in results[:max_solutions]
    ]

    if testV:
        return format_inventory_results(formatted)

    if compV:
        return formatted

    return formatted[:max_solutions]


def gen_full_solution(colors, operators, restrictions, goal, max_solutions=5, testV=False, required="", forbidden=""):
    try:
        if not colors or not operators:
            raise ValueError("Colors and operators cannot be empty")
        if not all(c in mapping for c in colors):
            raise ValueError("Invalid color specified")

        valid_restrictions = []
        try:
            valid_restrictions = comp_restrictions(colors, operators, restrictions, goal, req=required)
        except Exception as e:
            if testV:
                return f"Error generating restrictions: {str(e)}"
            raise

        valid_solutions = []
        try:
            valid_solutions = comp_solutions(colors, operators, goal, compV=True, req=required, forb=forbidden)
        except Exception as e:
            if testV:
                return f"Error generating solutions: {str(e)}"
            raise

        solutions = []
        for res_expr, res_cards in valid_restrictions:
            for sol_expr, sol_cards in valid_solutions:
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
                except Exception:
                    continue
            if len(solutions) >= max_solutions:
                break

        if testV:
            if not solutions:
                return "No valid solutions found matching all criteria 😭🥀"

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


def gen_full_solution_inventory(required_cubes, permitted_cubes, goal, max_solutions=5, testV=False, required_card="", forbidden=""):
    try:
        required_inv = parse_cube_inventory(required_cubes)
        permitted_inv = parse_cube_inventory(permitted_cubes)
        available_inv = required_inv + permitted_inv

        results = []

        if required_needs_restriction(required_inv):
            restriction_required = required_inv.copy()
            solution_required = strip_restriction_cubes(required_inv)

            valid_restrictions = collect_restriction_candidates(
                required_base=restriction_required,
                permitted_inv=permitted_inv,
                goal=goal,
                req_card=required_card
            )

            valid_solutions = collect_solution_candidates(
                required_base=solution_required,
                permitted_inv=permitted_inv,
                target_size=goal,
                req_card=required_card,
                forb_card=forbidden
            )

            for res in valid_restrictions:
                for sol in valid_solutions:
                    common_cards = intersect(res["cards"], sol["cards"])
                    if len(common_cards) != goal:
                        continue

                    if forbidden != "" and forbidden in common_cards:
                        continue
                    if required_card != "" and required_card not in common_cards:
                        continue

                    results.append({
                        "restriction": res["expr"],
                        "solution": sol["expr"],
                        "cards": common_cards
                    })

            results.sort(key=lambda x: (
                sum(expression_cube_usage(x["solution"]).values()) + sum(expression_cube_usage(x["restriction"]).values()),
                len(x["solution"]) + len(x["restriction"]),
                x["solution"],
                x["restriction"]
            ))
            results = results[:max_solutions]

        else:
            # Prefer shorter solution-only answers first
            solution_only = collect_solution_candidates(
                required_base=required_inv,
                permitted_inv=permitted_inv,
                target_size=goal,
                req_card=required_card,
                forb_card=forbidden
            )

            for sol in solution_only:
                results.append({
                    "solution": sol["expr"],
                    "cards": sol["cards"]
                })
                if len(results) >= max_solutions:
                    break

            # Optional restriction + solution answers if restriction cubes are available
            if len(results) < max_solutions and counter_total(available_inv, RESTRICTION_CUBES) > 0:
                restriction_required = required_inv.copy()
                solution_required = required_inv.copy()

                valid_restrictions = collect_restriction_candidates(
                    required_base=restriction_required,
                    permitted_inv=permitted_inv,
                    goal=goal,
                    req_card=required_card
                )

                valid_solutions = collect_solution_candidates(
                    required_base=solution_required,
                    permitted_inv=permitted_inv,
                    target_size=goal,
                    req_card=required_card,
                    forb_card=forbidden
                )

                optional_pairs = []
                for res in valid_restrictions:
                    for sol in valid_solutions:
                        common_cards = intersect(res["cards"], sol["cards"])
                        if len(common_cards) != goal:
                            continue

                        if forbidden != "" and forbidden in common_cards:
                            continue
                        if required_card != "" and required_card not in common_cards:
                            continue

                        optional_pairs.append({
                            "restriction": res["expr"],
                            "solution": sol["expr"],
                            "cards": common_cards
                        })

                optional_pairs.sort(key=lambda x: (
                    sum(expression_cube_usage(x["solution"]).values()) + sum(expression_cube_usage(x["restriction"]).values()),
                    len(x["solution"]) + len(x["restriction"]),
                    x["solution"],
                    x["restriction"]
                ))

                for item in optional_pairs:
                    if len(results) >= max_solutions:
                        break
                    results.append(item)

        if testV:
            return format_inventory_results(results)

        return results

    except Exception as e:
        if testV:
            return f"Calculation failed: {str(e)}"
        raise

def calc_full_solution(resexpr, solexpr):
    output = []
    if resexpr == "":
        if solexpr == "":
            return "Error: No inputs detected"
        else:
            sole = set_cards(solexpr)
            output.append(f"Solution set has {len(sole)} cards\n")
            output.append(f"    {', '.join(sole)}\n")
            return "\n".join(output)
    else:
        if solexpr == "":
            rese = parseR(resexpr)
            output.append(f"New universe has {len(rese)} cards\n")
            output.append(f"    {', '.join(rese)}\n")
            return "\n".join(output)
        else:
            fullsol = intersect(parseR(resexpr, calcV=True), set_cards(solexpr, calcV=True))
            output.append(f"Solution set has {len(fullsol)} cards\n")
            output.append(f"    {', '.join(fullsol)}\n")
            return "\n".join(output)
