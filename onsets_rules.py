"""Versioned On-Sets rule helpers used by Phase 1 tests and UI adapters.

This module intentionally stays small. The Phase 2 engine will own full parsing,
validation, and solving; these helpers make the rules that are already locked
testable without coupling them to Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Mapping, Sequence


RULESET_ID = "agloa-2026-27"


class Division(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    JUNIOR = "junior"
    SENIOR = "senior"
    CUSTOM = "custom"


class SolutionSituation(str, Enum):
    NOW = "now"
    IMPOSSIBLE = "impossible"
    FORCEOUT = "forceout"


UNIVERSE_RANGES = {
    Division.ELEMENTARY: (6, 12),
    Division.MIDDLE: (6, 12),
    Division.JUNIOR: (6, 12),
    Division.SENIOR: (10, 14),
}

AUTOMATIC_VARIATIONS = {
    Division.ELEMENTARY: frozenset(),
    Division.MIDDLE: frozenset(),
    Division.JUNIOR: frozenset(
        {
            "multiple_operations",
            "union_intersection_interchangeable",
            "universe_null_interchangeable",
        }
    ),
    Division.SENIOR: frozenset(
        {
            "multiple_operations",
            "union_intersection_interchangeable",
            "universe_null_interchangeable",
        }
    ),
    Division.CUSTOM: frozenset(),
}


def resource_cube_limit(situation: SolutionSituation) -> int | None:
    """Return the per-Solution Resource limit; ``None`` means no fixed limit."""

    if situation is SolutionSituation.NOW:
        return 1
    if situation is SolutionSituation.FORCEOUT:
        return 0
    return None


def resource_use_is_legal(situation: SolutionSituation, used_count: int) -> bool:
    if used_count < 0:
        raise ValueError("Resource cube usage cannot be negative.")
    limit = resource_cube_limit(situation)
    return limit is None or used_count <= limit


def no_null_restrictions_satisfied(
    removal_counts_by_restriction: Sequence[Sequence[int]],
) -> bool:
    """Check No Null removal counts for every independent Restriction and order.

    Each outer item represents one independent Restriction. Its inner counts are
    the cards it removes in every order in which the Restrictions can be applied.
    A chain is one Restriction, and its count is positive when any link removes a
    card. An empty outer sequence means no Restriction was written.
    """

    return all(
        bool(counts) and all(count > 0 for count in counts)
        for counts in removal_counts_by_restriction
    )


def two_solutions_satisfied(
    first_solution_cards: Sequence[str], second_solution_cards: Sequence[str]
) -> bool:
    """Return whether Solution 2 contains a physical card absent from Solution 1."""

    return bool(set(second_solution_cards) - set(first_solution_cards))


def card_constraints_satisfied(
    solution_cards: Sequence[str],
    *,
    required_card: str | None = None,
    forbidden_card: str | None = None,
) -> bool:
    cards = set(solution_cards)
    if required_card is not None and required_card not in cards:
        return False
    if forbidden_card is not None and forbidden_card in cards:
        return False
    return True


def universe_size_warning(division: Division, card_count: int) -> str | None:
    """Return a non-blocking tournament-size warning for a selected division."""

    if card_count < 0 or card_count > 16:
        raise ValueError("An On-Sets Universe must contain between 0 and 16 cards.")
    if division is Division.CUSTOM:
        return None

    minimum, maximum = UNIVERSE_RANGES[division]
    if minimum <= card_count <= maximum:
        return None
    return (
        f"{division.value.title()} tournament Universes contain {minimum}-{maximum} "
        f"cards; this custom Universe contains {card_count}."
    )


_SINGLE_CHARACTER_ALIASES = {
    "B": "B",
    "b": "B",
    "R": "R",
    "r": "R",
    "G": "G",
    "g": "G",
    "Y": "Y",
    "y": "Y",
    "V": "V",
    "v": "V",
    "Z": "Z",
    "z": "Z",
    "U": "u",
    "u": "u",
    "∪": "u",
    "n": "n",
    "∩": "n",
    "-": "-",
    "−": "-",
    "–": "-",
    "'": "'",
    "c": "c",
    "C": "c",
    "⊂": "c",
    "⊆": "c",
    "=": "=",
    "(": "(",
    "[": "(",
    "{": "(",
    ")": ")",
    "]": ")",
    "}": ")",
}


def normalize_notation(expression: str) -> str:
    """Normalize accepted input aliases to the legacy engine's compact syntax."""

    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression cannot be empty.")

    compact = "".join(expression.split())
    compact = compact.replace("/\\", "Z").replace("∅", "Z").replace("Ø", "Z")

    normalized = []
    for character in compact:
        try:
            normalized.append(_SINGLE_CHARACTER_ALIASES[character])
        except KeyError as exc:
            raise ValueError(f"Unknown On-Sets symbol: {character}") from exc
    return "".join(normalized)


@dataclass(frozen=True)
class _Node:
    kind: str
    value: str = ""
    left: "_Node | None" = None
    right: "_Node | None" = None

    def display(self) -> str:
        if self.kind == "atom":
            return self.value
        if self.kind == "prime":
            assert self.left is not None
            return f"{self.left.display()}'"
        assert self.left is not None and self.right is not None
        operator = {"u": "U", "n": "∩", "-": "−"}[self.value]
        return f"({self.left.display()} {operator} {self.right.display()})"


@dataclass(frozen=True)
class Interpretation:
    expression: str
    cards: tuple[str, ...]

    @property
    def value(self) -> int:
        return len(self.cards)


class _InterpretationParser:
    def __init__(self, expression: str, max_interpretations: int):
        self.expression = normalize_notation(expression)
        self.index = 0
        self.max_interpretations = max_interpretations

    def parse(self) -> tuple[_Node, ...]:
        nodes = self._parse_sequence(stop_at_close=False)
        if self.index != len(self.expression):
            raise ValueError(f"Unexpected symbol at position {self.index + 1}.")
        return nodes

    def _parse_sequence(self, stop_at_close: bool) -> tuple[_Node, ...]:
        terms: list[tuple[_Node, ...]] = [self._parse_term()]
        operators: list[str] = []

        while self.index < len(self.expression):
            symbol = self.expression[self.index]
            if symbol == ")":
                if stop_at_close:
                    break
                raise ValueError("Closing parenthesis has no matching opening parenthesis.")
            if symbol not in {"u", "n", "-"}:
                if symbol in {"c", "="}:
                    raise ValueError("Restriction operators are not valid inside a Set-Name.")
                raise ValueError(f"Expected a binary operation at position {self.index + 1}.")
            operators.append(symbol)
            self.index += 1
            terms.append(self._parse_term())

        choices = product(*terms)
        results: list[_Node] = []
        for selected_terms in choices:
            results.extend(self._all_binary_trees(selected_terms, tuple(operators)))
            if len(results) > self.max_interpretations:
                raise ValueError(
                    f"Expression has more than {self.max_interpretations} legal interpretations."
                )

        unique = {node.display(): node for node in results}
        return tuple(unique[key] for key in sorted(unique))

    def _parse_term(self) -> tuple[_Node, ...]:
        if self.index >= len(self.expression):
            raise ValueError("Expression cannot end with a binary operation.")

        symbol = self.expression[self.index]
        if symbol in "BRGYVZ":
            nodes = (_Node("atom", value=symbol),)
            self.index += 1
        elif symbol == "(":
            self.index += 1
            if self.index < len(self.expression) and self.expression[self.index] == ")":
                raise ValueError("Grouping symbols cannot be empty.")
            nodes = self._parse_sequence(stop_at_close=True)
            if self.index >= len(self.expression) or self.expression[self.index] != ")":
                raise ValueError("Opening parenthesis has no matching closing parenthesis.")
            self.index += 1
        elif symbol == "'":
            raise ValueError("Complement must follow a set or grouped expression.")
        else:
            raise ValueError(f"Expected a set at position {self.index + 1}.")

        while self.index < len(self.expression) and self.expression[self.index] == "'":
            nodes = tuple(_Node("prime", left=node) for node in nodes)
            self.index += 1
        return nodes

    def _all_binary_trees(
        self, terms: Sequence[_Node], operators: Sequence[str]
    ) -> tuple[_Node, ...]:
        if not operators:
            return (terms[0],)

        trees: list[_Node] = []
        for split, operator in enumerate(operators):
            left_trees = self._all_binary_trees(terms[: split + 1], operators[:split])
            right_trees = self._all_binary_trees(terms[split + 1 :], operators[split + 1 :])
            for left, right in product(left_trees, right_trees):
                trees.append(_Node("binary", value=operator, left=left, right=right))
        return tuple(trees)


def _evaluate(
    node: _Node,
    universe: Mapping[str, Sequence[str]],
    *,
    symmetric_difference: bool,
) -> set[str]:
    universe_cards = set(universe)
    if node.kind == "atom":
        if node.value == "V":
            return universe_cards
        if node.value == "Z":
            return set()
        color = node.value.lower()
        return {card for card, dots in universe.items() if color in dots}

    assert node.left is not None
    left = _evaluate(node.left, universe, symmetric_difference=symmetric_difference)
    if node.kind == "prime":
        return universe_cards - left

    assert node.right is not None
    right = _evaluate(node.right, universe, symmetric_difference=symmetric_difference)
    if node.value == "u":
        return left | right
    if node.value == "n":
        return left & right
    if symmetric_difference:
        return left ^ right
    return left - right


def enumerate_interpretations(
    expression: str,
    universe: Mapping[str, Sequence[str]],
    *,
    max_interpretations: int = 1_000,
    symmetric_difference: bool = False,
) -> tuple[Interpretation, ...]:
    """Return every grouping permitted by the expression's existing parentheses."""

    if max_interpretations < 1:
        raise ValueError("max_interpretations must be positive.")
    nodes = _InterpretationParser(expression, max_interpretations).parse()
    card_order = {card: index for index, card in enumerate(universe)}

    results = []
    for node in nodes:
        cards = tuple(
            sorted(
                _evaluate(
                    node,
                    universe,
                    symmetric_difference=symmetric_difference,
                ),
                key=card_order.__getitem__,
            )
        )
        results.append(Interpretation(expression=node.display(), cards=cards))
    return tuple(results)
