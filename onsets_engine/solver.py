"""Deterministic, bounded On-Sets solver built on the immutable domain engine."""

from __future__ import annotations

from collections import defaultdict
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
                cards, _ = evaluate(expression, universe, state.variations)
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
                        cards, _ = evaluate(expression, universe, state.variations)
                        add(cost, expression, cards)
        by_cost[cost].sort(key=lambda candidate: candidate.display)
    return tuple(tuple(level) for level in by_cost)


def _goal_value(cards: frozenset[str], state: GameState, doubled: frozenset[str]) -> int:
    return len(cards) + len(cards & doubled)


def _two_operations_satisfied(candidate: _Candidate, state: GameState) -> bool:
    if Variation.TWO_OPERATIONS not in state.variations.active:
        return True
    return sum(symbol in SET_OPERATIONS for symbol in candidate.symbols) >= 2


def _restriction_candidates(
    state: GameState,
    deadline: float,
    max_cost: int,
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

    found: dict[tuple[tuple[str, ...], tuple[tuple[str, int], ...]], _RestrictionCandidate] = {}
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
                key = (applied.remaining_cards, cube_use.physical.items)
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
) -> list[SolverAnswer]:
    answers: list[SolverAnswer] = []
    catalog = _catalog(active_universe, state, max_cost, deadline, per_key=1)
    for level in catalog[1:]:
        for candidate in level:
            if monotonic() > deadline:
                raise SearchTimedOut
            if not _two_operations_satisfied(candidate, state):
                continue
            if restriction is None and len(candidate.symbols) < 2:
                continue
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
            cube_use = match_cube_use(candidate.symbols, matching_state, required)
            if cube_use is None:
                continue
            if restriction and not combined_resource_use_is_legal(
                restriction.cube_use, cube_use, state
            ):
                continue
            value = _goal_value(candidate.cards, state, doubled)
            if value != state.goal:
                continue
            cards = tuple(card_id for card_id in active_universe.ids if card_id in candidate.cards)
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

    selected: list[SolverAnswer] = []
    # First pass intentionally promotes a distinct physical card set.
    for cards in ordered_keys:
        if len(selected) >= requested:
            break
        selected.append(buckets[cards][0])
    depth = 1
    while len(selected) < requested:
        added = False
        for cards in ordered_keys:
            if depth < len(buckets[cards]):
                selected.append(buckets[cards][depth])
                added = True
                if len(selected) >= requested:
                    break
        if not added:
            break
        depth += 1

    grouped: dict[tuple[str, ...], list[SolverAnswer]] = defaultdict(list)
    for answer in selected:
        grouped[answer.cards].append(answer)
    return tuple(
        SolutionGroup(cards, grouped[cards][0].value, tuple(grouped[cards]))
        for cards in ordered_keys
        if cards in grouped
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
                requested=max(2, requested),
                time_limit_seconds=per_assignment,
                max_solution_cubes=max_solution_cubes,
                max_restriction_cubes=max_restriction_cubes,
            )
            for group in report.groups:
                answers.extend(group.answers)
            if not report.search_complete:
                timed_out = True
        groups = _ordered_groups(answers, requested)
        returned = sum(len(group.answers) for group in groups)
        if timed_out:
            warnings.append(
                f"Blank Card Wild search shared the {time_limit_seconds:g}-second limit across 16 color assignments."
            )
        if returned >= requested:
            warnings.append("Stopped displaying at the requested Solution count; ask for more to continue exploring.")
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

    available, _ = _inventory_for_situation(state)
    if max_solution_cubes is None:
        required_set_name = _required_for_set_name(state, has_restriction=False)
        baseline = required_set_name.total
        required_binary_operations = sum(
            required_set_name.count(symbol) for symbol in ("u", "n", "-")
        )
        required_atoms = sum(
            required_set_name.count(symbol) for symbol in SET_SYMBOLS
        )
        minimum_well_formed = baseline + max(
            0,
            required_binary_operations + 1 - required_atoms,
        )
        max_solution_cubes = min(10, max(6, baseline + 4, minimum_well_formed))
    if max_restriction_cubes is None:
        max_restriction_cubes = min(9, max(5, state.required.total + 3))

    doubled = double_set_cards(state.universe, state.variations)
    answers: list[SolverAnswer] = []
    timed_out = False
    mandatory_restriction = state.required.count("c") + state.required.count("=") > 0
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
                )
            )

        # Mandatory Restrictions are always searched. Optional Restrictions are
        # searched when needed to fill the requested result count.
        if mandatory_restriction or len(answers) < requested:
            restrictions, simple_restrictions = _restriction_candidates(
                state,
                deadline,
                max_restriction_cubes,
            )
            for restriction in restrictions:
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
                    )
                )

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
                        )
                    )
    except SearchTimedOut:
        timed_out = True
        warnings.append(
            f"Search stopped at the {time_limit_seconds:g}-second interactive limit. Increase the limit to search farther."
        )

    groups = _ordered_groups(answers, requested)
    returned = sum(len(group.answers) for group in groups)
    if returned >= requested:
        warnings.append("Stopped displaying at the requested Solution count; ask for more to continue exploring.")
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
