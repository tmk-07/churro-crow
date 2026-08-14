"""FastAPI adapter that keeps HTTP concerns outside the rules engine."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from onsets_engine import (
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

from .schemas import CheckRequest, SolveRequest, VariationPayload


API_VERSION = "v1"

app = FastAPI(
    title="Churro Crow On-Sets API",
    version="1.0.0",
    description="Versioned HTTP access to the AGLOA On-Sets checker and solver.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,https://onsets.tkimify.com",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _unprocessable(message: str, issues: list[str] | None = None) -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={"message": message, "issues": issues or []},
    )


def _variation_config(payload: VariationPayload, division: Division) -> VariationConfig:
    return VariationConfig(
        active=with_automatic_variations(division, frozenset(payload.active)),
        wild_cube=payload.wild_cube,
        wild_cube_section=payload.wild_cube_section,
        wild_cube_ordinal=payload.wild_cube_ordinal,
        wild_as=payload.wild_as,
        blank_dots=frozenset(color.upper() for color in payload.blank_dots),
        blank_card_auto=payload.blank_card_auto,
        double_set_expression=payload.double_set_expression,
        double_set_uses_symmetric_difference=(
            payload.double_set_uses_symmetric_difference
        ),
        required_card=payload.required_card,
        forbidden_card=payload.forbidden_card,
    )


def _universe(card_ids: list[str], config: VariationConfig) -> Universe:
    if not card_ids:
        raise _unprocessable("Select at least one Universe card.")
    if len(card_ids) != len(set(card_ids)):
        raise _unprocessable("A Universe cannot contain duplicate physical cards.")
    unknown = sorted(set(card_ids) - set(CARD_ORDER))
    if unknown:
        raise _unprocessable(f"Unknown On-Sets cards: {', '.join(unknown)}.")
    try:
        return Universe.from_ids(card_ids, blank_dots=config.blank_dots)
    except ValueError as exc:
        raise _unprocessable(str(exc)) from exc


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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "api_version": API_VERSION,
        "ruleset_id": RULESET_ID,
    }


@app.get("/api/config")
def config() -> dict[str, Any]:
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


@app.post("/api/check")
def check(request: CheckRequest) -> dict[str, Any]:
    if not request.solution.strip() and not request.restriction.strip():
        raise _unprocessable("Enter a Restriction, a Set-Name, or both.")
    config = _variation_config(request.variations, request.division)
    universe = _universe(request.universe, config)
    issues = _variation_issues(
        request.division,
        universe,
        config,
        validate_cube_availability=False,
    )
    if issues and not request.proceed_anyway:
        raise _unprocessable(
            "Resolve the variation declaration or proceed anyway.", issues
        )
    warnings = list(issues)
    size_warning = universe_size_warning(request.division, len(universe.ids))
    if size_warning:
        warnings.append(size_warning)
    try:
        if not request.solution.strip():
            interpretations = []
            for restrictions in enumerate_restriction_sets(
                request.restriction,
                max_interpretations=request.max_interpretations,
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
            request.solution,
            restriction_text=request.restriction,
            variations=config,
            max_interpretations=request.max_interpretations,
        )
        doubled = double_set_cards(universe, config)
    except ValueError as exc:
        raise _unprocessable(str(exc)) from exc

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


@app.post("/api/solve")
def solve_endpoint(request: SolveRequest) -> dict[str, Any]:
    config = _variation_config(request.variations, request.division)
    try:
        cube_sections = {
            "required": CubeInventory.parse(request.required),
            "permitted": CubeInventory.parse(request.permitted),
            "forbidden": CubeInventory.parse(request.forbidden),
            "resources": CubeInventory.parse(request.resources),
        }
    except ValueError as exc:
        raise _unprocessable(str(exc)) from exc
    universe = _universe(request.universe, config)
    issues = _variation_issues(
        request.division,
        universe,
        config,
        cube_sections=cube_sections,
        validate_cube_availability=True,
    )
    if issues and not request.proceed_anyway:
        raise _unprocessable(
            "Resolve the variation declaration or proceed anyway.", issues
        )
    state = GameState(
        universe=universe,
        goal=request.goal,
        division=request.division,
        situation=request.situation,
        required=cube_sections["required"],
        permitted=cube_sections["permitted"],
        forbidden=cube_sections["forbidden"],
        resources=cube_sections["resources"],
        variations=config,
    )
    errors, state_warnings = validate_game_state(state)
    if errors:
        raise _unprocessable("The game state is invalid.", list(errors))
    try:
        report = solve(
            state,
            requested=request.requested,
            time_limit_seconds=request.time_limit_seconds,
            max_solution_cubes=request.max_solution_cubes,
            max_restriction_cubes=request.max_restriction_cubes,
        )
    except ValueError as exc:
        raise _unprocessable(str(exc)) from exc

    return {
        "api_version": API_VERSION,
        "ruleset_id": RULESET_ID,
        "requested": report.requested,
        "returned": report.returned,
        "search_complete": report.search_complete,
        "elapsed_seconds": report.elapsed_seconds,
        "warnings": list(dict.fromkeys(issues + list(state_warnings) + list(report.warnings))),
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
