"""Versioned variation availability and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .expressions import double_set_cards, parse_interpretations
from .models import CARD_ORDER, CubeInventory, Division, GameState, Situation, Universe, Variation, VariationConfig


AUTOMATIC_VARIATIONS = {
    Division.ELEMENTARY: frozenset(),
    Division.MIDDLE: frozenset(),
    Division.JUNIOR: frozenset({
        Variation.MULTIPLE_OPERATIONS,
        Variation.UNION_INTERSECTION_INTERCHANGEABLE,
        Variation.UNIVERSE_NULL_INTERCHANGEABLE,
    }),
    Division.SENIOR: frozenset({
        Variation.MULTIPLE_OPERATIONS,
        Variation.UNION_INTERSECTION_INTERCHANGEABLE,
        Variation.UNIVERSE_NULL_INTERCHANGEABLE,
    }),
    Division.CUSTOM: frozenset(),
}

AVAILABLE_VARIATIONS = {
    Division.ELEMENTARY: frozenset({
        Variation.WILD_CUBE,
        Variation.UNION_INTERSECTION_INTERCHANGEABLE,
        Variation.UNIVERSE_NULL_INTERCHANGEABLE,
        Variation.TWO_OPERATIONS,
        Variation.MULTIPLE_OPERATIONS,
    }),
    Division.MIDDLE: frozenset({
        Variation.WILD_CUBE,
        Variation.UNION_INTERSECTION_INTERCHANGEABLE,
        Variation.UNIVERSE_NULL_INTERCHANGEABLE,
        Variation.TWO_OPERATIONS,
        Variation.MULTIPLE_OPERATIONS,
        Variation.NO_NULL,
    }),
    Division.JUNIOR: frozenset({
        Variation.WILD_CUBE,
        Variation.TWO_OPERATIONS,
        Variation.NO_NULL,
        Variation.DOUBLE_SET,
        Variation.REQUIRED_FORBIDDEN_CARD,
        Variation.BLANK_CARD_WILD,
    }),
    Division.SENIOR: frozenset({
        Variation.WILD_CUBE,
        Variation.TWO_OPERATIONS,
        Variation.NO_NULL,
        Variation.DOUBLE_SET,
        Variation.REQUIRED_FORBIDDEN_CARD,
        Variation.BLANK_CARD_WILD,
        Variation.SYMMETRIC_DIFFERENCE,
    }),
    Division.CUSTOM: frozenset(Variation),
}

UNIVERSE_RANGES = {
    Division.ELEMENTARY: (6, 12),
    Division.MIDDLE: (6, 12),
    Division.JUNIOR: (6, 12),
    Division.SENIOR: (10, 14),
}


@dataclass(frozen=True, slots=True)
class VariationIssue:
    message: str
    blocking_without_override: bool = True


def with_automatic_variations(division: Division, selected: frozenset[Variation]) -> frozenset[Variation]:
    return selected | AUTOMATIC_VARIATIONS[division]


def universe_size_warning(division: Division, count: int) -> str | None:
    if not 0 <= count <= 16:
        raise ValueError("An On-Sets Universe contains between 0 and 16 physical cards.")
    if division is Division.CUSTOM:
        return None
    minimum, maximum = UNIVERSE_RANGES[division]
    if minimum <= count <= maximum:
        return None
    return f"{division.value.title()} tournament Universes contain {minimum}-{maximum} cards; this one contains {count}."


def validate_variations(
    division: Division,
    universe: Universe,
    config: VariationConfig,
    *,
    resources_symbols: tuple[str, ...] = (),
    cube_sections: Mapping[str, CubeInventory] | None = None,
    validate_cube_availability: bool = True,
) -> tuple[VariationIssue, ...]:
    issues: list[VariationIssue] = []
    unavailable = config.active - AVAILABLE_VARIATIONS[division] - AUTOMATIC_VARIATIONS[division]
    if unavailable:
        names = ", ".join(sorted(item.value.replace("_", " ").title() for item in unavailable))
        issues.append(VariationIssue(f"Not normally available in {division.value.title()}: {names}."))
    if (
        validate_cube_availability
        and config.enabled(Variation.NO_NULL)
        and not ({"c", "="} & set(resources_symbols))
    ):
        issues.append(VariationIssue("No Null Restrictions cannot affect this shake because Resources contains no ⊂ or = cube."))
    if validate_cube_availability and config.enabled(Variation.WILD_CUBE):
        if not config.wild_cube:
            issues.append(VariationIssue("Choose which physical cube is wild."))
        else:
            if cube_sections is not None:
                section = config.wild_cube_section or "resources"
                ordinal = config.wild_cube_ordinal or 1
                inventory = cube_sections.get(section, CubeInventory())
                if ordinal < 1 or inventory.count(config.wild_cube) < ordinal:
                    issues.append(VariationIssue("The selected Wild Cube is not present in its current section."))
            elif config.wild_cube not in resources_symbols:
                issues.append(VariationIssue("The selected Wild Cube is not present in the current cube state."))
            if division is not Division.ELEMENTARY and config.wild_cube in {"c", "="}:
                issues.append(VariationIssue("⊂ and = cannot be selected as Wild Cubes outside Elementary."))
    if config.enabled(Variation.BLANK_CARD_WILD) and "blank" not in universe.ids:
        issues.append(VariationIssue("Blank Card Wild cannot affect a Universe without the blank card."))
    if config.enabled(Variation.DOUBLE_SET):
        if not config.double_set_expression:
            issues.append(VariationIssue("Enter the set that counts double."))
        else:
            try:
                normalized_symbols = parse_interpretations(config.double_set_expression)[0].written_symbols()
                if len(normalized_symbols) > 4:
                    issues.append(VariationIssue("A Double Set declaration may use at most four cube symbols."))
                doubled = double_set_cards(universe, config)
                if not doubled or doubled == frozenset(universe.ids):
                    issues.append(VariationIssue("The Double Set must be nonempty and cannot equal the Universe."))
            except (ValueError, IndexError) as exc:
                issues.append(VariationIssue(f"Invalid Double Set declaration: {exc}"))
    if config.required_card and config.required_card not in CARD_ORDER:
        issues.append(VariationIssue("The required card is not a physical On-Sets card."))
    if config.forbidden_card and config.forbidden_card not in CARD_ORDER:
        issues.append(VariationIssue("The forbidden card is not a physical On-Sets card."))
    if config.required_card and config.required_card not in universe.ids:
        issues.append(VariationIssue("The required card is not in the selected Universe."))
    if config.forbidden_card and config.forbidden_card not in universe.ids:
        issues.append(VariationIssue("The forbidden card is not in the selected Universe."))
    if (
        config.enabled(Variation.BLANK_CARD_WILD)
        and config.forbidden_card == "blank"
    ):
        issues.append(VariationIssue("Blank Card Wild conflicts with Blank Card Forbidden."))
    return tuple(issues)


def card_constraints_satisfied(cards: tuple[str, ...], universe: Universe, config: VariationConfig) -> bool:
    selected = set(cards)
    if config.required_card and config.required_card not in selected:
        return False
    if config.forbidden_card and config.forbidden_card in selected:
        return False
    if config.enabled(Variation.BLANK_CARD_WILD) and config.blank_dots:
        effective = "".join(color for color in "BRGY" if color in config.blank_dots) or "blank"
        if config.forbidden_card == effective and "blank" in selected:
            return False
    return True


def validate_game_state(state: GameState) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return blocking errors and non-blocking procedural warnings."""

    all_cubes = state.required + state.permitted + state.forbidden + state.resources
    errors: list[str] = []
    warnings: list[str] = []
    color_count = sum(all_cubes.count(symbol) for symbol in "BRGY")
    operation_count = sum(all_cubes.count(symbol) for symbol in ("u", "n", "-", "'"))
    restriction_count = sum(all_cubes.count(symbol) for symbol in ("V", "Z", "c", "="))
    if color_count > 8:
        errors.append(f"The shake contains {color_count} color cubes, but an On-Sets set has 8.")
    if operation_count > 4:
        errors.append(f"The shake contains {operation_count} operation cubes, but an On-Sets set has 4.")
    if restriction_count > 3:
        errors.append(f"The shake contains {restriction_count} V/Z/Restriction cubes, but an On-Sets set has 3.")
    if state.situation is Situation.NOW:
        if state.resources.total < 2:
            warnings.append("An official Now challenge requires at least two cubes to remain in Resources.")
        if state.required.total + state.permitted.total == 0:
            warnings.append("An official Now challenge requires at least one cube in Required or Permitted.")
    if state.situation is Situation.FORCEOUT and state.resources.total:
        warnings.append("Forceout occurs after Resources is empty; entered Resource cubes will be ignored.")
    if state.division is Division.ELEMENTARY and any(
        all_cubes.count(symbol) for symbol in ("c", "=")
    ):
        warnings.append("Elementary On-Sets does not use ⊂ or = Restriction cubes.")
    return tuple(errors), tuple(warnings)
