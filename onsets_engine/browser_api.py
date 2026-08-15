"""JSON adapter for running the On-Sets engine inside Pyodide.

This module intentionally depends only on the standard library and the domain
engine.  It mirrors the FastAPI response contract without importing FastAPI or
Pydantic, so the same calculation code can execute in a browser Web Worker.
"""

from __future__ import annotations

import json
from typing import Any

from . import (
    AUTOMATIC_VARIATIONS,
    AVAILABLE_VARIATIONS,
    CARD_ORDER,
    RULESET_ID,
    CubeInventory,
    Division,
    GameState,
    Situation,
    Universe,
    Variation,
    VariationConfig,
    apply_restrictions,
    check_expression,
    double_set_cards,
    enumerate_restriction_sets,
    solve,
    universe_size_warning,
    validate_game_state,
    validate_variations,
    with_automatic_variations,
)


API_VERSION = "v1"


class BrowserRequestError(ValueError):
    """A user-facing request error with optional reviewable issues."""

    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        super().__init__(message)
        self.issues = issues or []


def _enum(enum_type: type[Any], value: Any, default: Any) -> Any:
    try:
        return enum_type(value if value is not None else default.value)
    except (TypeError, ValueError) as exc:
        raise BrowserRequestError(f"Unknown {enum_type.__name__.lower()}: {value}.") from exc


def _integer(
    payload: dict[str, Any],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    try:
        value = int(payload.get(name, default))
    except (TypeError, ValueError) as exc:
        raise BrowserRequestError(f"{name.replace('_', ' ').title()} must be a number.") from exc
    if not minimum <= value <= maximum:
        raise BrowserRequestError(
            f"{name.replace('_', ' ').title()} must be between {minimum} and {maximum}."
        )
    return value


def _optional_integer(
    payload: dict[str, Any],
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    value = payload.get(name)
    if value is None:
        return None
    return _integer(payload, name, minimum, minimum=minimum, maximum=maximum)


def _seconds(payload: dict[str, Any]) -> float:
    try:
        value = float(payload.get("time_limit_seconds", 5.0))
    except (TypeError, ValueError) as exc:
        raise BrowserRequestError("Time Limit Seconds must be a number.") from exc
    if not 0 < value <= 60:
        raise BrowserRequestError("Time Limit Seconds must be greater than 0 and at most 60.")
    return value


def _variations(payload: Any, division: Division) -> VariationConfig:
    data = payload if isinstance(payload, dict) else {}
    try:
        selected = frozenset(Variation(item) for item in data.get("active", []))
    except (TypeError, ValueError) as exc:
        raise BrowserRequestError("One or more selected variations are unknown.") from exc
    blank_dots = frozenset(str(color).upper() for color in data.get("blank_dots", []))
    return VariationConfig(
        active=with_automatic_variations(division, selected),
        wild_cube=data.get("wild_cube"),
        wild_cube_section=data.get("wild_cube_section"),
        wild_cube_ordinal=data.get("wild_cube_ordinal"),
        wild_as=data.get("wild_as"),
        blank_dots=blank_dots,
        blank_card_auto=bool(data.get("blank_card_auto", False)),
        double_set_expression=data.get("double_set_expression"),
        double_set_uses_symmetric_difference=bool(
            data.get("double_set_uses_symmetric_difference", False)
        ),
        required_card=data.get("required_card"),
        forbidden_card=data.get("forbidden_card"),
    )


def _universe(card_ids: Any, config: VariationConfig) -> Universe:
    if not isinstance(card_ids, list) or not card_ids:
        raise BrowserRequestError("Select at least one Universe card.")
    if len(card_ids) != len(set(card_ids)):
        raise BrowserRequestError("A Universe cannot contain duplicate physical cards.")
    unknown = sorted(set(card_ids) - set(CARD_ORDER))
    if unknown:
        raise BrowserRequestError(f"Unknown On-Sets cards: {', '.join(unknown)}.")
    return Universe.from_ids(card_ids, blank_dots=config.blank_dots)


def _variation_issues(
    division: Division,
    universe: Universe,
    config: VariationConfig,
    *,
    cube_sections: dict[str, CubeInventory] | None = None,
    validate_cube_availability: bool,
) -> list[str]:
    return [
        issue.message
        for issue in validate_variations(
            division,
            universe,
            config,
            cube_sections=cube_sections,
            validate_cube_availability=validate_cube_availability,
        )
    ]


def _steps(steps: Any) -> list[dict[str, Any]]:
    return [
        {
            "expression": step.expression,
            "cards": list(step.cards),
            "explanation": step.explanation,
        }
        for step in steps
    ]


def _cube_use(cube_use: Any) -> dict[str, Any] | None:
    if cube_use is None:
        return None
    return {
        "written": cube_use.written.as_dict(),
        "physical": cube_use.physical.as_dict(),
        "resource_cubes": cube_use.resource_cubes,
        "resource_inventory": cube_use.resource_inventory.as_dict(),
        "wild_cube_used": cube_use.wild_cube_used,
        "wild_cube_id": cube_use.wild_cube_id,
        "wild_cube_as": cube_use.wild_cube_as,
        "notes": list(cube_use.notes),
    }


def config_response() -> dict[str, Any]:
    return {
        "api_version": API_VERSION,
        "ruleset_id": RULESET_ID,
        "card_order": list(CARD_ORDER),
        "divisions": [division.value for division in Division],
        "situations": [situation.value for situation in Situation],
        "variations": [variation.value for variation in Variation],
        "available_variations": {
            division.value: sorted(item.value for item in AVAILABLE_VARIATIONS[division])
            for division in Division
        },
        "automatic_variations": {
            division.value: sorted(item.value for item in AUTOMATIC_VARIATIONS[division])
            for division in Division
        },
    }


def check_response(payload: dict[str, Any]) -> dict[str, Any]:
    solution_text = str(payload.get("solution", ""))
    restriction_text = str(payload.get("restriction", ""))
    if not solution_text.strip() and not restriction_text.strip():
        raise BrowserRequestError("Enter a Restriction, a Set-Name, or both.")
    division = _enum(Division, payload.get("division"), Division.CUSTOM)
    config = _variations(payload.get("variations"), division)
    universe = _universe(payload.get("universe"), config)
    issues = _variation_issues(
        division,
        universe,
        config,
        validate_cube_availability=False,
    )
    if issues and not payload.get("proceed_anyway", False):
        raise BrowserRequestError(
            "Resolve the variation declaration or proceed anyway.", issues
        )
    warnings = list(issues)
    size_warning = universe_size_warning(division, len(universe.ids))
    if size_warning:
        warnings.append(size_warning)
    max_interpretations = _integer(
        payload,
        "max_interpretations",
        1_000,
        minimum=1,
        maximum=5_000,
    )

    if not solution_text.strip():
        interpretations = []
        for restrictions in enumerate_restriction_sets(
            restriction_text,
            max_interpretations=max_interpretations,
        ):
            active, details = apply_restrictions(restrictions, universe, config)
            interpretations.append({
                "remaining_universe": list(active.ids),
                "restrictions": [
                    {
                        "expression": detail.expression,
                        "remaining_cards": list(detail.remaining_cards),
                        "removed_cards": list(detail.removed_cards),
                        "link_removals": list(detail.link_removals),
                    }
                    for detail in details
                ],
            })
        return {
            "api_version": API_VERSION,
            "ruleset_id": RULESET_ID,
            "warnings": warnings,
            "answers": [],
            "restriction_interpretations": interpretations,
        }

    answers = check_expression(
        universe,
        solution_text,
        restriction_text=restriction_text,
        variations=config,
        max_interpretations=max_interpretations,
    )
    doubled = double_set_cards(universe, config)
    sorted_answers = sorted(
        answers,
        key=lambda answer: (
            answer.solution.value,
            answer.solution.expression,
            answer.restriction or "",
        ),
    )
    return {
        "api_version": API_VERSION,
        "ruleset_id": RULESET_ID,
        "warnings": warnings,
        "answers": [
            {
                "restriction": answer.restriction,
                "expression": answer.solution.expression,
                "cards": list(answer.solution.cards),
                "doubled_cards": [
                    card for card in answer.solution.cards if card in doubled
                ],
                "value": answer.solution.value,
                "restricted_universe": list(answer.restricted_universe),
                "violations": list(answer.violations),
                "steps": _steps(answer.solution.steps),
            }
            for answer in sorted_answers
        ],
        "restriction_interpretations": [],
    }


def solve_response(payload: dict[str, Any]) -> dict[str, Any]:
    division = _enum(Division, payload.get("division"), Division.CUSTOM)
    situation = _enum(Situation, payload.get("situation"), Situation.IMPOSSIBLE)
    config = _variations(payload.get("variations"), division)
    cube_sections = {
        section: CubeInventory.parse(str(payload.get(section, "")))
        for section in ("required", "permitted", "forbidden", "resources")
    }
    universe = _universe(payload.get("universe"), config)
    issues = _variation_issues(
        division,
        universe,
        config,
        cube_sections=cube_sections,
        validate_cube_availability=True,
    )
    if issues and not payload.get("proceed_anyway", False):
        raise BrowserRequestError(
            "Resolve the variation declaration or proceed anyway.", issues
        )
    goal = _integer(payload, "goal", 0, minimum=0, maximum=10_000)
    state = GameState(
        universe=universe,
        goal=goal,
        division=division,
        situation=situation,
        required=cube_sections["required"],
        permitted=cube_sections["permitted"],
        forbidden=cube_sections["forbidden"],
        resources=cube_sections["resources"],
        variations=config,
    )
    errors, state_warnings = validate_game_state(state)
    if errors:
        raise BrowserRequestError("The game state is invalid.", list(errors))
    report = solve(
        state,
        requested=_integer(payload, "requested", 5, minimum=1, maximum=100),
        time_limit_seconds=_seconds(payload),
        max_solution_cubes=_optional_integer(
            payload, "max_solution_cubes", minimum=2, maximum=20
        ),
        max_restriction_cubes=_optional_integer(
            payload, "max_restriction_cubes", minimum=3, maximum=24
        ),
    )
    return {
        "api_version": API_VERSION,
        "ruleset_id": RULESET_ID,
        "requested": report.requested,
        "returned": report.returned,
        "search_complete": report.search_complete,
        "elapsed_seconds": report.elapsed_seconds,
        "warnings": list(
            dict.fromkeys(issues + list(state_warnings) + list(report.warnings))
        ),
        "groups": [
            {
                "cards": list(group.cards),
                "doubled_cards": list(group.answers[0].doubled_cards),
                "value": group.value,
                "answers": [
                    {
                        "solution": answer.solution,
                        "restriction": answer.restriction,
                        "cards": list(answer.cards),
                        "doubled_cards": list(answer.doubled_cards),
                        "value": answer.value,
                        "cube_count": answer.cube_count,
                        "cube_use": _cube_use(answer.cube_use),
                        "restriction_cube_use": _cube_use(answer.restriction_cube_use),
                        "resource_inventory": answer.resource_inventory.as_dict(),
                        "variation_notes": list(answer.variation_notes),
                        "steps": _steps(answer.steps),
                    }
                    for answer in group.answers
                ],
            }
            for group in report.groups
        ],
    }


def dispatch(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    if method == "config":
        return config_response()
    if method == "check":
        return check_response(payload)
    if method == "solve":
        return solve_response(payload)
    raise BrowserRequestError(f"Unknown browser engine method: {method}.")


def dispatch_json(method: str, payload_json: str) -> str:
    """Return a JSON envelope that is safe to pass through the JS bridge."""

    try:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise BrowserRequestError("The calculation request must be an object.")
        data = dispatch(method, payload)
        envelope = {"ok": True, "data": data}
    except BrowserRequestError as exc:
        envelope = {"ok": False, "message": str(exc), "issues": exc.issues}
    except ValueError as exc:
        envelope = {"ok": False, "message": str(exc), "issues": []}
    return json.dumps(envelope)
