"""Deterministic, bounded On-Sets solver built on the immutable domain engine."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from dataclasses import replace
from itertools import combinations, product
from time import monotonic

from .expressions import Expr, double_set_cards, evaluate
from .models import (
    CubeInventory,
    CubeUse,
    GameState,
    SET_OPERATIONS,
    SET_SYMBOLS,
    Situation,
    SolutionGroup,
    SolverAnswer,
    SolverReport,
    Universe,
    Variation,
    VariationConfig,
)
from .restrictions import (
    Restriction,
    RestrictionLink,
    apply_restriction,
    apply_restrictions,
    no_null_satisfied_for_every_order,
)
from .variations import card_constraints_satisfied


class SearchTimedOut(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _Candidate:
    expression: Expr
    cards: frozenset[str]

    @property
    def symbols(self) -> tuple[str, ...]:
        return self.expression.written_symbols()

    @property
    def display(self) -> str:
        return self.expression.display()


@dataclass(frozen=True, slots=True)
class _RestrictionCandidate:
    restrictions: tuple[Restriction, ...]
    remaining: tuple[str, ...]
    cube_use: CubeUse

    @property
    def display(self) -> str:
        return "; ".join(restriction.display() for restriction in self.restrictions)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(
            symbol
            for restriction in self.restrictions
            for symbol in restriction.written_symbols()
        )


_WILD_SOURCE = "__wild_cube__"


def _inventory_for_situation(state: GameState) -> tuple[CubeInventory, int | None]:
    on_mat = state.required + state.permitted
    if state.situation is Situation.NOW:
        return on_mat + state.resources, 1
    if state.situation is Situation.IMPOSSIBLE:
        return on_mat + state.resources, None
    return on_mat, 0


def _required_for_set_name(state: GameState, *, has_restriction: bool) -> CubeInventory:
    if has_restriction:
        return state.required.without({"c", "="})
    return state.required


def _counts(symbols: tuple[str, ...]) -> CubeInventory:
    counts: dict[str, int] = {}
    for symbol in symbols:
        counts[symbol] = counts.get(symbol, 0) + 1
    return CubeInventory.from_mapping(counts)


def _minimum_set_name_cost(required: CubeInventory, *, roots: int = 1) -> int:
    """Smallest well-formed expression containing the required non-relation cubes."""

    binary = sum(required.count(symbol) for symbol in ("u", "n", "-"))
    unary = required.count("'")
    atoms = sum(required.count(symbol) for symbol in SET_SYMBOLS)
    # A forest with ``roots`` Set-Names and ``binary`` binary operations needs
    # exactly binary + roots operands. Required atom cubes can supply those
    # operands; any shortfall must come from Permitted/Resource cubes.
    return binary + unary + max(atoms, binary + roots)


def _minimum_restriction_cost(state: GameState, relation_count: int) -> int:
    required_set_symbols = state.required.without({"c", "="})
    return relation_count + _minimum_set_name_cost(
        required_set_symbols,
        roots=relation_count + 1,
    )


def _wild_location(state: GameState) -> tuple[str, str, int] | None:
    config = state.variations
    if Variation.WILD_CUBE not in config.active or not config.wild_cube:
        return None
    return (
        config.wild_cube_section or "resources",
        config.wild_cube,
        config.wild_cube_ordinal or 1,
    )


def _section_inventory(state: GameState, section: str) -> CubeInventory:
    return {
        "required": state.required,
        "permitted": state.permitted,
        "forbidden": state.forbidden,
        "resources": state.resources,
    }.get(section, CubeInventory())


def _wild_is_available(state: GameState) -> bool:
    location = _wild_location(state)
    if location is None:
        return False
    section, symbol, ordinal = location
    if ordinal > _section_inventory(state, section).count(symbol):
        return False
    if section == "forbidden":
        return False
    if section == "resources" and state.situation is Situation.FORCEOUT:
        return False
    return section in {"required", "permitted", "resources"}


def _symbol_counts_can_match(
    symbols: tuple[str, ...],
    state: GameState,
    required: CubeInventory,
) -> bool:
    """Fast inventory feasibility check used before the full cube assignment.

    The definitive check remains :func:`match_cube_use`. This helper groups the
    two interchangeable symbol pairs and accounts for MOPS and a fixed Wild
    interpretation without constructing the assignment product.
    """

    available, _ = _inventory_for_situation(state)
    available_counts = available.as_dict()
    required_counts = required.as_dict()
    written = Counter(symbols)
    active = state.variations.active

    families: list[tuple[str, ...]] = []
    grouped: set[str] = set()
    if Variation.UNION_INTERSECTION_INTERCHANGEABLE in active:
        families.append(("u", "n"))
        grouped.update(("u", "n"))
    if Variation.UNIVERSE_NULL_INTERCHANGEABLE in active:
        families.append(("V", "Z"))
        grouped.update(("V", "Z"))
    families.extend((symbol,) for symbol in SET_SYMBOLS + SET_OPERATIONS + ("c", "=") if symbol not in grouped)

    wild_location = _wild_location(state)
    wild_available = _wild_is_available(state)
    wild_section = wild_location[0] if wild_location else None
    wild_face = wild_location[1] if wild_location else None
    wild_as = state.variations.wild_as
    if wild_available and wild_face:
        available_counts[wild_face] = available_counts.get(wild_face, 0) - 1
        if wild_section == "required":
            required_counts[wild_face] = required_counts.get(wild_face, 0) - 1

    wild_choices = (False,)
    if wild_available and wild_as:
        wild_choices = (True,) if wild_section == "required" else (False, True)

    multiple_operations = Variation.MULTIPLE_OPERATIONS in active
    for use_wild in wild_choices:
        legal = True
        for family in families:
            occurrences = sum(written[symbol] for symbol in family)
            if use_wild and wild_as in family:
                occurrences -= 1
            required_occurrences = sum(max(0, required_counts.get(symbol, 0)) for symbol in family)
            available_occurrences = sum(max(0, available_counts.get(symbol, 0)) for symbol in family)
            is_operation_family = all(symbol in SET_OPERATIONS for symbol in family)
            if occurrences < required_occurrences:
                legal = False
                break
            if multiple_operations and is_operation_family:
                if occurrences and available_occurrences < 1:
                    legal = False
                    break
            elif occurrences > available_occurrences:
                legal = False
                break
        if not legal:
            continue
        if use_wild and not any(
            wild_as in family and any(written[symbol] for symbol in family)
            for family in families
        ):
            continue
        return True
    return False


def _source_options(math_symbol: str, state: GameState, wild_as: str | None) -> tuple[str, ...]:
    options = [math_symbol]
    active = state.variations.active
    if Variation.UNION_INTERSECTION_INTERCHANGEABLE in active:
        if math_symbol == "u":
            options.append("n")
        elif math_symbol == "n":
            options.append("u")
    if Variation.UNIVERSE_NULL_INTERCHANGEABLE in active:
        if math_symbol == "V":
            options.append("Z")
        elif math_symbol == "Z":
            options.append("V")
    wild_can_write = wild_as == math_symbol
    if Variation.UNION_INTERSECTION_INTERCHANGEABLE in active:
        wild_can_write = wild_can_write or (math_symbol, wild_as) in {
            ("u", "n"),
            ("n", "u"),
        }
    if Variation.UNIVERSE_NULL_INTERCHANGEABLE in active:
        wild_can_write = wild_can_write or (math_symbol, wild_as) in {
            ("V", "Z"),
            ("Z", "V"),
        }
    if _wild_is_available(state) and wild_can_write:
        options.append(_WILD_SOURCE)
    return tuple(dict.fromkeys(options))


def _wild_targets(state: GameState, symbols: tuple[str, ...]) -> tuple[str | None, ...]:
    if not _wild_is_available(state):
        return (None,)
    if state.variations.wild_as:
        return (state.variations.wild_as,)
    # A wild cube has one consistent meaning throughout a Solution. Trying only
    # symbols actually written avoids an unnecessary 12-way multiplier.
    face = state.variations.wild_cube
    return tuple(dict.fromkeys((None, face) + symbols))


def match_cube_use(
    symbols: tuple[str, ...],
    state: GameState,
    required: CubeInventory,
) -> CubeUse | None:
    """Match written mathematical symbols to physical cubes and situation limits."""

    available, resource_limit = _inventory_for_situation(state)
    on_mat = state.required + state.permitted
    multiple_operations = Variation.MULTIPLE_OPERATIONS in state.variations.active
    best: CubeUse | None = None
    wild_location = _wild_location(state)
    wild_available = _wild_is_available(state)
    wild_section = wild_location[0] if wild_location else None
    wild_face = wild_location[1] if wild_location else None

    ordinary_available = available.as_dict()
    ordinary_on_mat = on_mat.as_dict()
    required_ordinary = required.as_dict()
    if wild_available and wild_face:
        ordinary_available[wild_face] = ordinary_available.get(wild_face, 0) - 1
        if wild_section in {"required", "permitted"}:
            ordinary_on_mat[wild_face] = ordinary_on_mat.get(wild_face, 0) - 1
        if wild_section == "required":
            required_ordinary[wild_face] = required_ordinary.get(wild_face, 0) - 1

    for wild_as in _wild_targets(state, symbols):
        option_lists = [_source_options(symbol, state, wild_as) for symbol in symbols]
        # Reject impossible branches before constructing the product.
        if any(not any(
            (source == _WILD_SOURCE and wild_available)
            or ordinary_available.get(source, 0) > 0
            for source in options
        ) for options in option_lists):
            continue
        for assignment in product(*option_lists):
            wild_math_symbols = [
                math_symbol
                for math_symbol, source in zip(symbols, assignment)
                if source == _WILD_SOURCE
            ]
            if wild_math_symbols:
                if any(
                    _WILD_SOURCE not in _source_options(symbol, state, wild_as)
                    for symbol in wild_math_symbols
                ):
                    continue
                if not (
                    multiple_operations
                    and wild_as in SET_OPERATIONS
                ) and len(wild_math_symbols) > 1:
                    continue
            assigned: dict[str, list[str]] = defaultdict(list)
            for math_symbol, physical_symbol in zip(symbols, assignment):
                if physical_symbol != _WILD_SOURCE:
                    assigned[physical_symbol].append(math_symbol)

            physical_counts: dict[str, int] = {}
            legal = True
            for physical_symbol, math_symbols in assigned.items():
                occurrences = len(math_symbols)
                operation_occurrences = sum(symbol in SET_OPERATIONS for symbol in math_symbols)
                non_operation_occurrences = occurrences - operation_occurrences
                if multiple_operations and operation_occurrences:
                    needed = non_operation_occurrences + max(
                        1,
                        required_ordinary.get(physical_symbol, 0) - non_operation_occurrences,
                    )
                    if occurrences < required_ordinary.get(physical_symbol, 0):
                        legal = False
                        break
                else:
                    needed = occurrences
                physical_counts[physical_symbol] = needed
                if needed > ordinary_available.get(physical_symbol, 0):
                    legal = False
                    break
            if not legal:
                continue
            if any(
                physical_counts.get(symbol, 0) < count
                for symbol, count in required_ordinary.items()
                if count > 0
            ):
                continue
            wild_used = bool(wild_math_symbols)
            if wild_section == "required" and not wild_used:
                continue

            ordinary_resource_counts = {
                symbol: max(0, count - ordinary_on_mat.get(symbol, 0))
                for symbol, count in physical_counts.items()
            }
            wild_from_resources = wild_used and wild_section == "resources"
            resource_used = sum(ordinary_resource_counts.values()) + int(wild_from_resources)
            if resource_limit is not None and resource_used > resource_limit:
                continue

            displayed_physical = dict(physical_counts)
            if wild_used and wild_face:
                displayed_physical[wild_face] = displayed_physical.get(wild_face, 0) + 1
            displayed_resources = dict(ordinary_resource_counts)
            if wild_from_resources and wild_face:
                displayed_resources[wild_face] = displayed_resources.get(wild_face, 0) + 1

            notes: list[str] = []
            if wild_used and wild_as and wild_face and wild_as != wild_face:
                notes.append(
                    f"{wild_face} Wild ({state.variations.wild_cube_id}) is used as {wild_as}."
                )
            if Variation.UNION_INTERSECTION_INTERCHANGEABLE in state.variations.active:
                swaps = sum(
                    (math, source) in {("u", "n"), ("n", "u")}
                    for math, source in zip(symbols, assignment)
                )
                if swaps:
                    notes.append("Uses U/∩ interchangeable.")
            if Variation.UNIVERSE_NULL_INTERCHANGEABLE in state.variations.active:
                swaps = sum(
                    (math, source) in {("V", "Z"), ("Z", "V")}
                    for math, source in zip(symbols, assignment)
                )
                if swaps:
                    notes.append("Uses V/Z interchangeable.")
            use = CubeUse(
                written=_counts(symbols),
                physical=CubeInventory.from_mapping(displayed_physical),
                resource_cubes=resource_used,
                resource_inventory=CubeInventory.from_mapping(displayed_resources),
                ordinary_resource_inventory=CubeInventory.from_mapping(ordinary_resource_counts),
                wild_cube_used=wild_used,
                wild_cube_id=state.variations.wild_cube_id if wild_used else None,
                wild_cube_as=wild_as if wild_used else None,
                wild_cube_from_resources=wild_from_resources,
                notes=tuple(notes),
            )
            if best is None or (use.resource_cubes, use.physical.total, use.notes) < (
                best.resource_cubes,
                best.physical.total,
                best.notes,
            ):
                best = use
    return best


def _written_symbols_available(state: GameState) -> tuple[tuple[str, ...], tuple[str, ...]]:
    available, _ = _inventory_for_situation(state)
    atoms: list[str] = []
    operations: list[str] = []
    all_math = SET_SYMBOLS + SET_OPERATIONS
    for symbol in all_math:
        targets = _wild_targets(state, (symbol,))
        if any(
            any(
                (source == _WILD_SOURCE and _wild_is_available(state))
                or available.count(source)
                for source in _source_options(symbol, state, target)
            )
            for target in targets
        ):
            (atoms if symbol in SET_SYMBOLS else operations).append(symbol)
    return tuple(atoms), tuple(operations)


def _catalog(
    universe: Universe,
    state: GameState,
    max_cost: int,
    deadline: float,
    *,
    per_key: int = 1,
) -> tuple[tuple[_Candidate, ...], ...]:
    """Generate expressions by cube count, deduplicating semantic/inventory twins."""

    atoms, operations = _written_symbols_available(state)
    universe_cards = frozenset(universe.ids)
    by_cost: list[list[_Candidate]] = [[] for _ in range(max_cost + 1)]
    seen_by_cost: list[dict[tuple[frozenset[str], tuple[str, ...]], int]] = [
        {} for _ in range(max_cost + 1)
    ]

    def add(cost: int, expression: Expr, cards: frozenset[str]) -> None:
        signature = (cards, tuple(sorted(expression.written_symbols())))
        count = seen_by_cost[cost].get(signature, 0)
        if count >= per_key:
            return
        seen_by_cost[cost][signature] = count + 1
        by_cost[cost].append(_Candidate(expression, cards))

    for atom in atoms:
        expression = Expr.atom(atom)
        cards, _ = evaluate(expression, universe, state.variations)
        add(1, expression, cards)

    for cost in range(2, max_cost + 1):
        if monotonic() > deadline:
            raise SearchTimedOut
        if "'" in operations:
            for child in by_cost[cost - 1]:
                expression = Expr.complement(child.expression)
                cards = universe_cards - child.cards
                add(cost, expression, cards)
        for operation in (symbol for symbol in operations if symbol != "'"):
            for left_cost in range(1, cost - 1):
                right_cost = cost - left_cost - 1
                if right_cost < 1:
                    continue
                for left in by_cost[left_cost]:
                    for right in by_cost[right_cost]:
                        if monotonic() > deadline:
                            raise SearchTimedOut
                        expression = Expr.binary(operation, left.expression, right.expression)
                        if operation == "u":
                            cards = left.cards | right.cards
                        elif operation == "n":
                            cards = left.cards & right.cards
                        elif Variation.SYMMETRIC_DIFFERENCE in state.variations.active:
                            cards = left.cards ^ right.cards
                        else:
                            cards = left.cards - right.cards
                        add(cost, expression, cards)
        by_cost[cost].sort(key=lambda candidate: candidate.display)
    return tuple(tuple(level) for level in by_cost)


def _goal_value(cards: frozenset[str], state: GameState, doubled: frozenset[str]) -> int:
    return len(cards) + len(cards & doubled)


def _two_operations_satisfied(candidate: _Candidate, state: GameState) -> bool:
    if Variation.TWO_OPERATIONS not in state.variations.active:
        return True
    return sum(symbol in SET_OPERATIONS for symbol in candidate.symbols) >= 2


def _canonical_chain_candidates(
    state: GameState,
    relation_symbols: tuple[str, ...],
    deadline: float,
    max_cost: int,
    min_relations: int,
    max_relations: int,
) -> tuple[_RestrictionCandidate, ...]:
    """Generate deep legal chains without a Cartesian product of every side.

    Multiple Required relation cubes commonly appear as identity links followed
    by one substantive link, for example ``R = R = R ⊂ expression``. Keeping
    the repeated side atomic lets the remaining side carry the Required
    operation cubes and reaches long official-style statements efficiently.
    """

    catalog_state = state
    if (
        _wild_is_available(state)
        and state.variations.wild_cube
        and state.variations.wild_as is None
    ):
        # A declared Wild cube is allowed to retain its shown face. Search that
        # ordinary interpretation first; broader Wild meanings remain available
        # to the fallback search.
        catalog_state = replace(
            state,
            variations=replace(state.variations, wild_as=state.variations.wild_cube),
        )

    largest_complex_side = max_cost - (2 * min_relations)
    if largest_complex_side < 1:
        return ()
    catalog = _catalog(
        state.universe,
        catalog_state,
        largest_complex_side,
        deadline,
        per_key=1,
    )
    anchors = catalog[1]
    found: dict[
        tuple[tuple[str, ...], tuple[tuple[str, int], ...], str | None],
        _RestrictionCandidate,
    ] = {}
    preferred_limit = 128
    required_relations = Counter({
        symbol: state.required.count(symbol)
        for symbol in ("c", "=")
    })

    def operation_profile(symbols: tuple[str, ...]) -> tuple[int, int, int]:
        counts = Counter(symbols)
        return (counts["u"] + counts["n"], counts["-"], counts["'"])

    required_operation_profile = operation_profile(
        tuple(
            symbol
            for symbol in SET_OPERATIONS
            for _ in range(state.required.count(symbol))
        )
    )

    for relation_count in range(min_relations, max_relations + 1):
        minimum_cost = _minimum_restriction_cost(state, relation_count)
        largest_side = max_cost - (2 * relation_count)
        if minimum_cost > max_cost or largest_side < 1:
            continue
        operator_sequences = sorted(
            set(product(relation_symbols, repeat=relation_count)),
            key=lambda operators: (tuple(operator == "c" for operator in operators), operators),
        )
        for total_cost in range(minimum_cost, max_cost + 1):
            complex_cost = total_cost - (2 * relation_count)
            if not 1 <= complex_cost <= largest_side:
                continue
            for operators in operator_sequences:
                operator_counts = Counter(operators)
                if relation_count == sum(required_relations.values()) and any(
                    operator_counts[symbol] != required_relations[symbol]
                    for symbol in ("c", "=")
                ):
                    continue
                for anchor in anchors:
                    for complex_side in catalog[complex_cost]:
                        if (
                            total_cost == minimum_cost
                            and operation_profile(complex_side.symbols)
                            != required_operation_profile
                        ):
                            continue
                        for sides in (
                            (anchor,) * relation_count + (complex_side,),
                            (complex_side,) + (anchor,) * relation_count,
                        ):
                            symbols_list = list(sides[0].symbols)
                            for index, operator in enumerate(operators):
                                symbols_list.append(operator)
                                symbols_list.extend(sides[index + 1].symbols)
                            symbols = tuple(symbols_list)
                            if not _symbol_counts_can_match(
                                symbols,
                                catalog_state,
                                state.required,
                            ):
                                continue
                            cube_use = match_cube_use(
                                symbols,
                                catalog_state,
                                state.required,
                            )
                            if cube_use is None:
                                continue
                            restriction = Restriction(tuple(
                                RestrictionLink(
                                    sides[index].expression,
                                    operator,
                                    sides[index + 1].expression,
                                )
                                for index, operator in enumerate(operators)
                            ))
                            applied = apply_restriction(
                                restriction,
                                state.universe,
                                state.variations,
                            )
                            if Variation.NO_NULL in state.variations.active and not any(
                                count > 0 for count in applied.link_removals
                            ):
                                continue
                            key = (
                                applied.remaining_cards,
                                cube_use.physical.items,
                                cube_use.wild_cube_as,
                            )
                            candidate = _RestrictionCandidate(
                                (restriction,),
                                applied.remaining_cards,
                                cube_use,
                            )
                            previous = found.get(key)
                            if previous is None or (
                                len(candidate.symbols),
                                candidate.display,
                            ) < (
                                len(previous.symbols),
                                previous.display,
                            ):
                                found[key] = candidate
                                if len(found) >= preferred_limit:
                                    return tuple(sorted(
                                        found.values(),
                                        key=lambda item: (len(item.symbols), item.display),
                                    ))
                            if monotonic() > deadline:
                                raise SearchTimedOut
    return tuple(sorted(
        found.values(),
        key=lambda item: (len(item.symbols), item.display),
    ))


def _restriction_candidates(
    state: GameState,
    deadline: float,
    max_cost: int,
    *,
    canonical_only: bool = False,
) -> tuple[tuple[_RestrictionCandidate, ...], tuple[Restriction, ...]]:
    available, _ = _inventory_for_situation(state)
    relation_symbols = tuple(
        symbol
        for symbol in ("c", "=")
        if any(
            any(
                (source == _WILD_SOURCE and _wild_is_available(state))
                or available.count(source)
                for source in _source_options(symbol, state, target)
            )
            for target in _wild_targets(state, (symbol,))
        )
    )
    if not relation_symbols:
        return (), ()
    # Sides are intentionally shallow first. This produces the shortest useful
    # restrictions while keeping interactive search bounded.
    side_cost = min(4, max(1, (max_cost - 1) // 2))
    catalog = _catalog(state.universe, state, side_cost, deadline, per_key=1)
    sides = [candidate for level in catalog[1:] for candidate in level]
    # Prefer a diverse set of semantic sides rather than many syntactic twins.
    semantic_sides: dict[frozenset[str], _Candidate] = {}
    for candidate in sides:
        semantic_sides.setdefault(candidate.cards, candidate)
    sides = sorted(semantic_sides.values(), key=lambda item: (len(item.symbols), item.display))

    # Keep one-link statements as raw building blocks even when a statement by
    # itself cannot consume every Required cube. The fallback pass validates
    # the combined inventory of two or three independent statements.
    simple_pool: dict[str, Restriction] = {}
    for operator in relation_symbols:
        for left in sides:
            for right in sides:
                if monotonic() > deadline:
                    raise SearchTimedOut
                restriction = Restriction((RestrictionLink(left.expression, operator, right.expression),))
                if len(restriction.written_symbols()) <= max_cost:
                    simple_pool.setdefault(restriction.display(), restriction)

    found: dict[
        tuple[tuple[str, ...], tuple[tuple[str, int], ...], str | None],
        _RestrictionCandidate,
    ] = {}
    relation_capacity = sum(available.count(symbol) for symbol in ("c", "="))
    if (
        _wild_is_available(state)
        and state.variations.wild_cube not in {"c", "="}
        and state.variations.wild_as in {None, "c", "="}
    ):
        relation_capacity += 1
    max_relations = min(3, relation_capacity)
    required_relations = sum(state.required.count(symbol) for symbol in ("c", "="))
    min_relations = max(1, required_relations)
    for candidate in _canonical_chain_candidates(
        state,
        relation_symbols,
        deadline,
        max_cost,
        min_relations,
        max_relations,
    ):
        found[(
            candidate.remaining,
            candidate.cube_use.physical.items,
            candidate.cube_use.wild_cube_as,
        )] = candidate
    if canonical_only and found:
        candidates = tuple(sorted(
            found.values(),
            key=lambda item: (len(item.symbols), item.display),
        ))
        simple = tuple(simple_pool[key] for key in sorted(simple_pool))
        return candidates, simple
    for relation_count in range(min_relations, max_relations + 1):
        if relation_count > 1:
            chain_sides = [candidate for candidate in sides if len(candidate.symbols) == 1]
        else:
            chain_sides = sides
        for operators in product(relation_symbols, repeat=relation_count):
            for selected in product(chain_sides, repeat=relation_count + 1):
                if monotonic() > deadline:
                    raise SearchTimedOut
                links = tuple(
                    RestrictionLink(selected[index].expression, operator, selected[index + 1].expression)
                    for index, operator in enumerate(operators)
                )
                restriction = Restriction(links)
                symbols = restriction.written_symbols()
                if len(symbols) > max_cost:
                    continue
                cube_use = match_cube_use(symbols, state, state.required)
                if cube_use is None:
                    continue
                applied = apply_restriction(restriction, state.universe, state.variations)
                if Variation.NO_NULL in state.variations.active and not any(
                    count > 0 for count in applied.link_removals
                ):
                    continue
                key = (
                    applied.remaining_cards,
                    cube_use.physical.items,
                    cube_use.wild_cube_as,
                )
                candidate = _RestrictionCandidate((restriction,), applied.remaining_cards, cube_use)
                previous = found.get(key)
                if previous is None or len(symbols) < len(previous.symbols):
                    found[key] = candidate
    candidates = tuple(sorted(found.values(), key=lambda item: (len(item.symbols), item.display)))
    simple = tuple(simple_pool[key] for key in sorted(simple_pool))
    return candidates, simple


def _independent_restriction_candidates(
    state: GameState,
    simple: tuple[Restriction, ...],
    deadline: float,
    max_cost: int,
) -> tuple[_RestrictionCandidate, ...]:
    """Build independent statements only for the solver's fallback pass."""

    unique_simple = {restriction.display(): restriction for restriction in simple}
    ordered = tuple(unique_simple[key] for key in sorted(unique_simple))
    found: dict[
        tuple[tuple[str, ...], tuple[tuple[str, int], ...]],
        _RestrictionCandidate,
    ] = {}
    available, _ = _inventory_for_situation(state)
    max_statements = min(
        3,
        sum(available.count(symbol) for symbol in ("c", "="))
        + int(
            _wild_is_available(state)
            and state.variations.wild_cube not in {"c", "="}
            and state.variations.wild_as in {None, "c", "="}
        ),
    )
    for statement_count in range(2, max_statements + 1):
        for selected in combinations(ordered, statement_count):
            if monotonic() > deadline:
                raise SearchTimedOut
            symbols = tuple(
                symbol
                for restriction in selected
                for symbol in restriction.written_symbols()
            )
            if len(symbols) > max_cost:
                continue
            cube_use = match_cube_use(symbols, state, state.required)
            if cube_use is None:
                continue
            if (
                Variation.NO_NULL in state.variations.active
                and not no_null_satisfied_for_every_order(
                    selected, state.universe, state.variations
                )
            ):
                continue
            active, _ = apply_restrictions(selected, state.universe, state.variations)
            key = (active.ids, cube_use.physical.items)
            candidate = _RestrictionCandidate(selected, active.ids, cube_use)
            previous = found.get(key)
            if previous is None or (len(candidate.symbols), candidate.display) < (
                len(previous.symbols),
                previous.display,
            ):
                found[key] = candidate
    return tuple(sorted(found.values(), key=lambda item: (len(item.symbols), item.display)))


def _answers_for_universe(
    state: GameState,
    active_universe: Universe,
    required: CubeInventory,
    doubled: frozenset[str],
    deadline: float,
    max_cost: int,
    *,
    restriction: _RestrictionCandidate | None = None,
    catalog_cache: dict[
        tuple[VariationConfig, int],
        tuple[tuple[_Candidate, ...], ...],
    ] | None = None,
    cube_use_cache: dict[
        tuple[VariationConfig, tuple[str, ...], CubeInventory],
        CubeUse | None,
    ] | None = None,
) -> list[SolverAnswer]:
    answers: list[SolverAnswer] = []
    matching_state = state
    if (
        restriction
        and restriction.cube_use.wild_cube_used
        and not state.variations.wild_as
    ):
        matching_state = replace(
            state,
            variations=replace(
                state.variations,
                wild_as=restriction.cube_use.wild_cube_as,
            ),
        )
    catalog_key = (matching_state.variations, max_cost)
    catalog = catalog_cache.get(catalog_key) if catalog_cache is not None else None
    if catalog is None:
        # Set expressions commute with restricting the Universe: evaluate once
        # on the original cards, then project each result onto the active cards.
        # This avoids rebuilding the same expression catalog for every candidate
        # Restriction.
        catalog = _catalog(
            state.universe,
            matching_state,
            max_cost,
            deadline,
            per_key=1,
        )
        if catalog_cache is not None:
            catalog_cache[catalog_key] = catalog
    active_ids = frozenset(active_universe.ids)
    for level in catalog[1:]:
        for candidate in level:
            if monotonic() > deadline:
                raise SearchTimedOut
            if not _two_operations_satisfied(candidate, state):
                continue
            if restriction is None and len(candidate.symbols) < 2:
                continue
            use_key = (matching_state.variations, candidate.symbols, required)
            if cube_use_cache is not None and use_key in cube_use_cache:
                cube_use = cube_use_cache[use_key]
            else:
                cube_use = match_cube_use(candidate.symbols, matching_state, required)
                if cube_use_cache is not None:
                    cube_use_cache[use_key] = cube_use
            if cube_use is None:
                continue
            if restriction and not combined_resource_use_is_legal(
                restriction.cube_use, cube_use, state
            ):
                continue
            projected_cards = candidate.cards & active_ids
            value = _goal_value(projected_cards, state, doubled)
            if value != state.goal:
                continue
            cards = tuple(card_id for card_id in active_universe.ids if card_id in projected_cards)
            if not card_constraints_satisfied(cards, active_universe, state.variations):
                continue
            _, steps = evaluate(candidate.expression, active_universe, state.variations)
            notes = list(cube_use.notes)
            if Variation.BLANK_CARD_WILD in state.variations.active:
                dots = "".join(color for color in "BRGY" if color in state.variations.blank_dots)
                notes.append(f"Blank card is treated as {dots or 'blank'}.")
            if doubled:
                notes.append("Cards in the declared Double Set count twice.")
            answers.append(
                SolverAnswer(
                    solution=candidate.display,
                    cards=cards,
                    value=value,
                    cube_use=cube_use,
                    restriction=restriction.display if restriction else None,
                    restriction_cube_use=restriction.cube_use if restriction else None,
                    variation_notes=tuple(dict.fromkeys(notes)),
                    steps=steps,
                )
            )
    return answers


def combined_resource_use_is_legal(
    restriction_use: CubeUse,
    solution_use: CubeUse,
    state: GameState,
) -> bool:
    """The same Resource cube may be reused across both written parts."""

    if (
        restriction_use.wild_cube_used
        and solution_use.wild_cube_used
        and restriction_use.wild_cube_id == solution_use.wild_cube_id
        and restriction_use.wild_cube_as != solution_use.wild_cube_as
    ):
        return False

    combined_ordinary: dict[str, int] = {}
    for symbol in set(restriction_use.ordinary_resource_inventory.symbols) | set(
        solution_use.ordinary_resource_inventory.symbols
    ):
        combined_ordinary[symbol] = max(
            restriction_use.ordinary_resource_inventory.count(symbol),
            solution_use.ordinary_resource_inventory.count(symbol),
        )
    # Compatibility for CubeUse values created by older callers/tests.
    if not combined_ordinary and not (
        restriction_use.wild_cube_from_resources
        or solution_use.wild_cube_from_resources
    ):
        for symbol in set(restriction_use.resource_inventory.symbols) | set(
            solution_use.resource_inventory.symbols
        ):
            combined_ordinary[symbol] = max(
                restriction_use.resource_inventory.count(symbol),
                solution_use.resource_inventory.count(symbol),
            )
    combined = dict(combined_ordinary)
    wild_from_resources = (
        restriction_use.wild_cube_from_resources
        or solution_use.wild_cube_from_resources
    )
    if wild_from_resources and state.variations.wild_cube:
        face = state.variations.wild_cube
        combined[face] = combined.get(face, 0) + 1
    inventory = CubeInventory.from_mapping(combined)
    if not state.resources.contains(inventory):
        return False
    if state.situation is Situation.NOW:
        return inventory.total <= 1
    if state.situation is Situation.FORCEOUT:
        return inventory.total == 0
    return True


def _distinct_card_set_count(answers: list[SolverAnswer]) -> int:
    return len({answer.cards for answer in answers})


def _ordered_groups(answers: list[SolverAnswer], requested: int) -> tuple[SolutionGroup, ...]:
    answers.sort(key=lambda answer: (
        answer.cube_count,
        len(answer.restriction or "") + len(answer.solution),
        answer.cards,
        answer.restriction or "",
        answer.solution,
    ))
    unique_answers: list[SolverAnswer] = []
    seen = set()
    for answer in answers:
        key = (answer.restriction, answer.solution, answer.cards, answer.cube_use.physical.items)
        if key not in seen:
            seen.add(key)
            unique_answers.append(answer)

    buckets: dict[tuple[str, ...], list[SolverAnswer]] = defaultdict(list)
    for answer in unique_answers:
        buckets[answer.cards].append(answer)
    ordered_keys = sorted(
        buckets,
        key=lambda cards: (
            buckets[cards][0].cube_count,
            len(buckets[cards][0].solution),
            cards,
        ),
    )

    selected_keys = ordered_keys[:requested]
    # Written alternatives are useful, but they do not consume a requested
    # Solution slot. Keep a compact set of the shortest alternatives under each
    # distinct physical card set.
    alternatives_per_card_set = 5
    return tuple(
        SolutionGroup(
            cards,
            buckets[cards][0].value,
            tuple(buckets[cards][:alternatives_per_card_set]),
        )
        for cards in selected_keys
    )


def solve(
    state: GameState,
    *,
    requested: int = 5,
    time_limit_seconds: float = 5.0,
    max_solution_cubes: int | None = None,
    max_restriction_cubes: int | None = None,
) -> SolverReport:
    if requested < 1:
        raise ValueError("Request at least one Solution.")
    if time_limit_seconds <= 0:
        raise ValueError("Search time must be positive.")
    started = monotonic()
    deadline = started + time_limit_seconds
    if (
        Variation.BLANK_CARD_WILD in state.variations.active
        and state.variations.blank_card_auto
        and "blank" in state.universe.ids
    ):
        answers: list[SolverAnswer] = []
        warnings: list[str] = []
        assignments = tuple(
            frozenset(color for index, color in enumerate("BRGY") if mask & (1 << index))
            for mask in range(16)
        )
        timed_out = False
        for index, dots in enumerate(assignments):
            remaining = deadline - monotonic()
            if remaining <= 0:
                timed_out = True
                break
            per_assignment = max(0.05, remaining / (len(assignments) - index))
            config = replace(
                state.variations,
                blank_dots=dots,
                blank_card_auto=False,
            )
            assignment_state = replace(
                state,
                universe=Universe.from_ids(state.universe.ids, blank_dots=dots),
                variations=config,
            )
            report = solve(
                assignment_state,
                requested=requested,
                time_limit_seconds=per_assignment,
                max_solution_cubes=max_solution_cubes,
                max_restriction_cubes=max_restriction_cubes,
            )
            for group in report.groups:
                answers.extend(group.answers)
            if not report.search_complete:
                timed_out = True
        groups = _ordered_groups(answers, requested)
        returned = len(groups)
        if timed_out:
            warnings.append(
                f"Blank Card Wild search shared the {time_limit_seconds:g}-second limit across 16 color assignments."
            )
        if returned >= requested:
            warnings.append(
                "Stopped displaying at the requested unique card-set count; ask for more to continue exploring."
            )
        return SolverReport(
            groups=groups,
            requested=requested,
            returned=returned,
            search_complete=not timed_out,
            elapsed_seconds=monotonic() - started,
            warnings=tuple(warnings),
        )

    warnings: list[str] = []
    if state.situation is Situation.FORCEOUT and state.resources.total:
        warnings.append("Forceout has no Resource cubes; the entered Resources were ignored.")

    mandatory_restriction = state.required.count("c") + state.required.count("=") > 0
    if max_solution_cubes is None:
        required_set_name = _required_for_set_name(
            state,
            has_restriction=mandatory_restriction,
        )
        minimum_well_formed = _minimum_set_name_cost(required_set_name)
        max_solution_cubes = min(
            12,
            max(6, required_set_name.total + 4, minimum_well_formed),
        )
    if max_restriction_cubes is None:
        required_relations = sum(state.required.count(symbol) for symbol in ("c", "="))
        relation_count = max(1, required_relations)
        minimum_well_formed = _minimum_restriction_cost(state, relation_count)
        max_restriction_cubes = min(
            17,
            max(5, state.required.total + 3, minimum_well_formed),
        )

    doubled = double_set_cards(state.universe, state.variations)
    answers: list[SolverAnswer] = []
    catalog_cache: dict[
        tuple[VariationConfig, int],
        tuple[tuple[_Candidate, ...], ...],
    ] = {}
    cube_use_cache: dict[
        tuple[VariationConfig, tuple[str, ...], CubeInventory],
        CubeUse | None,
    ] = {}
    timed_out = False
    try:
        if not mandatory_restriction:
            required = _required_for_set_name(state, has_restriction=False)
            answers.extend(
                _answers_for_universe(
                    state,
                    state.universe,
                    required,
                    doubled,
                    deadline,
                    max_solution_cubes,
                    catalog_cache=catalog_cache,
                    cube_use_cache=cube_use_cache,
                )
            )

        # Mandatory Restrictions are always searched. Optional Restrictions are
        # searched when needed to fill the requested distinct card-set count.
        if mandatory_restriction or _distinct_card_set_count(answers) < requested:
            restrictions, simple_restrictions = _restriction_candidates(
                state,
                deadline,
                max_restriction_cubes,
                canonical_only=True,
            )
            restrictions = tuple(sorted(
                restrictions,
                key=lambda restriction: (
                    not card_constraints_satisfied(
                        restriction.remaining,
                        state.universe.restrict_to(restriction.remaining),
                        state.variations,
                    ),
                    abs(
                        _goal_value(
                            frozenset(restriction.remaining),
                            state,
                            doubled,
                        )
                        - state.goal
                    ),
                    len(restriction.symbols),
                    restriction.display,
                ),
            ))
            searched_restrictions: set[
                tuple[str, tuple[str, ...], tuple[tuple[str, int], ...], str | None]
            ] = set()
            for restriction in restrictions:
                if monotonic() > deadline:
                    raise SearchTimedOut
                search_key = (
                    restriction.display,
                    restriction.remaining,
                    restriction.cube_use.physical.items,
                    restriction.cube_use.wild_cube_as,
                )
                searched_restrictions.add(search_key)
                active = state.universe.restrict_to(restriction.remaining)
                required = _required_for_set_name(state, has_restriction=True)
                answers.extend(
                    _answers_for_universe(
                        state,
                        active,
                        required,
                        doubled,
                        deadline,
                        max_solution_cubes,
                        restriction=restriction,
                        catalog_cache=catalog_cache,
                        cube_use_cache=cube_use_cache,
                    )
                )
                if _distinct_card_set_count(answers) >= requested:
                    break

            # If the fast canonical chain shape did not fill the request, use
            # the broader side/chain catalog with the remaining time budget.
            if _distinct_card_set_count(answers) < requested:
                fallback_restrictions, fallback_simple = _restriction_candidates(
                    state,
                    deadline,
                    max_restriction_cubes,
                )
                fallback_restrictions = tuple(sorted(
                    fallback_restrictions,
                    key=lambda restriction: (
                        not card_constraints_satisfied(
                            restriction.remaining,
                            state.universe.restrict_to(restriction.remaining),
                            state.variations,
                        ),
                        abs(
                            _goal_value(
                                frozenset(restriction.remaining),
                                state,
                                doubled,
                            )
                            - state.goal
                        ),
                        len(restriction.symbols),
                        restriction.display,
                    ),
                ))
                simple_restrictions = tuple(dict.fromkeys(
                    simple_restrictions + fallback_simple
                ))
                for restriction in fallback_restrictions:
                    if monotonic() > deadline:
                        raise SearchTimedOut
                    search_key = (
                        restriction.display,
                        restriction.remaining,
                        restriction.cube_use.physical.items,
                        restriction.cube_use.wild_cube_as,
                    )
                    if search_key in searched_restrictions:
                        continue
                    searched_restrictions.add(search_key)
                    active = state.universe.restrict_to(restriction.remaining)
                    required = _required_for_set_name(state, has_restriction=True)
                    answers.extend(
                        _answers_for_universe(
                            state,
                            active,
                            required,
                            doubled,
                            deadline,
                            max_solution_cubes,
                            restriction=restriction,
                            catalog_cache=catalog_cache,
                            cube_use_cache=cube_use_cache,
                        )
                    )
                    if _distinct_card_set_count(answers) >= requested:
                        break

            # Independent statements are deliberately a reserve strategy. They
            # are only explored when solution-only and regular/chain searches
            # produced no answer at all.
            if not answers:
                independent = _independent_restriction_candidates(
                    state,
                    simple_restrictions,
                    deadline,
                    max_restriction_cubes,
                )
                for restriction in independent:
                    if monotonic() > deadline:
                        raise SearchTimedOut
                    active = state.universe.restrict_to(restriction.remaining)
                    required = _required_for_set_name(state, has_restriction=True)
                    answers.extend(
                        _answers_for_universe(
                            state,
                            active,
                            required,
                            doubled,
                            deadline,
                            max_solution_cubes,
                            restriction=restriction,
                            catalog_cache=catalog_cache,
                            cube_use_cache=cube_use_cache,
                        )
                    )
    except SearchTimedOut:
        timed_out = True
        warnings.append(
            f"Search stopped at the {time_limit_seconds:g}-second interactive limit. Increase the limit to search farther."
        )

    groups = _ordered_groups(answers, requested)
    returned = len(groups)
    if returned >= requested:
        warnings.append(
            "Stopped displaying at the requested unique card-set count; ask for more to continue exploring."
        )
    elif state.situation is Situation.IMPOSSIBLE and not answers:
        warnings.append("Nothing was found.")
    elapsed = monotonic() - started
    return SolverReport(
        groups=groups,
        requested=requested,
        returned=returned,
        search_complete=not timed_out,
        elapsed_seconds=elapsed,
        warnings=tuple(warnings),
    )
