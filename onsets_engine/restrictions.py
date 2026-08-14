"""Restriction parsing, interpretation, and application."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations, product

from .expressions import Expr, evaluate, parse_interpretations
from .models import RestrictionResult, Universe, VariationConfig
from .notation import display_symbol, normalize_expression


@dataclass(frozen=True, slots=True)
class RestrictionLink:
    left: Expr
    operator: str
    right: Expr


@dataclass(frozen=True, slots=True)
class Restriction:
    links: tuple[RestrictionLink, ...]

    def display(self) -> str:
        parts = [self.links[0].left.display()]
        for link in self.links:
            parts.extend((display_symbol(link.operator), link.right.display()))
        return " ".join(parts)

    def written_symbols(self) -> tuple[str, ...]:
        parts = list(self.links[0].left.written_symbols())
        for link in self.links:
            parts.append(link.operator)
            parts.extend(link.right.written_symbols())
        return tuple(parts)


def split_independent(text: str) -> tuple[str, ...]:
    if not text or not text.strip():
        return ()
    statements: list[str] = []
    current: list[str] = []
    depth = 0
    for character in text:
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth -= 1
        if depth == 0 and character in ",;\n":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(character)
    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return tuple(statements)


def parse_restriction_interpretations(text: str, *, max_interpretations: int = 1_000) -> tuple[Restriction, ...]:
    normalized = normalize_expression(text)
    sides: list[str] = []
    operators: list[str] = []
    depth = 0
    start = 0
    for index, symbol in enumerate(normalized):
        if symbol == "(":
            depth += 1
        elif symbol == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("Closing parenthesis has no matching opening parenthesis.")
        elif symbol in {"c", "="}:
            if depth:
                raise ValueError("Grouping symbols may not enclose a Restriction operator.")
            sides.append(normalized[start:index])
            operators.append(symbol)
            start = index + 1
    if depth:
        raise ValueError("Opening parenthesis has no matching closing parenthesis.")
    sides.append(normalized[start:])
    if not operators:
        raise ValueError("A Restriction must contain ⊂ or =.")
    if any(not side for side in sides):
        raise ValueError("Every Restriction operator needs a Set-Name on both sides.")

    parsed_sides = [parse_interpretations(side, max_interpretations=max_interpretations) for side in sides]
    results: list[Restriction] = []
    for selected in product(*parsed_sides):
        links = tuple(
            RestrictionLink(selected[index], operator, selected[index + 1])
            for index, operator in enumerate(operators)
        )
        results.append(Restriction(links))
        if len(results) > max_interpretations:
            raise ValueError(f"Restriction has more than {max_interpretations} legal interpretations.")
    unique = {restriction.display(): restriction for restriction in results}
    return tuple(unique[key] for key in sorted(unique))


def apply_restriction(
    restriction: Restriction,
    universe: Universe,
    variations: VariationConfig = VariationConfig(),
) -> RestrictionResult:
    keep = set(universe.ids)
    link_removals: list[int] = []
    for link in restriction.links:
        left, _ = evaluate(link.left, universe, variations)
        right, _ = evaluate(link.right, universe, variations)
        if link.operator == "c":
            invalid = set(left) - set(right)
        else:
            invalid = set(left) ^ set(right)
        link_removals.append(len(keep & invalid))
        keep.difference_update(invalid)
    remaining = tuple(card_id for card_id in universe.ids if card_id in keep)
    removed = tuple(card_id for card_id in universe.ids if card_id not in keep)
    return RestrictionResult(restriction.display(), remaining, removed, tuple(link_removals))


def apply_restrictions(
    restrictions: tuple[Restriction, ...],
    universe: Universe,
    variations: VariationConfig = VariationConfig(),
) -> tuple[Universe, tuple[RestrictionResult, ...]]:
    active = universe
    results: list[RestrictionResult] = []
    for restriction in restrictions:
        result = apply_restriction(restriction, active, variations)
        results.append(result)
        active = active.restrict_to(result.remaining_cards)
    return active, tuple(results)


def no_null_satisfied_for_every_order(
    restrictions: tuple[Restriction, ...],
    universe: Universe,
    variations: VariationConfig,
) -> bool:
    if not restrictions:
        return True
    for order in permutations(restrictions):
        active = universe
        for restriction in order:
            result = apply_restriction(restriction, active, variations)
            if not any(count > 0 for count in result.link_removals):
                return False
            active = active.restrict_to(result.remaining_cards)
    return True


def enumerate_restriction_sets(text: str, *, max_interpretations: int = 1_000) -> tuple[tuple[Restriction, ...], ...]:
    statements = split_independent(text)
    if not statements:
        return ((),)
    choices = [parse_restriction_interpretations(statement, max_interpretations=max_interpretations) for statement in statements]
    combinations = tuple(product(*choices))
    if len(combinations) > max_interpretations:
        raise ValueError(f"Restrictions have more than {max_interpretations} legal interpretations.")
    return combinations
