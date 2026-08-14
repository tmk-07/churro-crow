"""Structured checker service independent of Streamlit."""

from __future__ import annotations

from .expressions import enumerate_evaluations, parse_interpretations
from .models import CheckedAnswer, Universe, Variation, VariationConfig
from .restrictions import apply_restrictions, enumerate_restriction_sets, no_null_satisfied_for_every_order
from .variations import card_constraints_satisfied


def check_expression(
    universe: Universe,
    solution: str,
    *,
    restriction_text: str = "",
    variations: VariationConfig = VariationConfig(),
    max_interpretations: int = 1_000,
) -> tuple[CheckedAnswer, ...]:
    restriction_sets = enumerate_restriction_sets(restriction_text, max_interpretations=max_interpretations)
    answers: list[CheckedAnswer] = []
    for restrictions in restriction_sets:
        base_violations: list[str] = []
        if variations.enabled(Variation.NO_NULL) and not no_null_satisfied_for_every_order(
            restrictions, universe, variations
        ):
            base_violations.append(
                "No Null Restrictions is not satisfied in every application order."
            )
        active, _ = apply_restrictions(restrictions, universe, variations)
        restriction_display = "; ".join(item.display() for item in restrictions) or None
        for result in enumerate_evaluations(
            solution,
            active,
            variations,
            max_interpretations=max_interpretations,
            weight_universe=universe,
        ):
            violations = list(base_violations)
            if not card_constraints_satisfied(result.cards, active, variations):
                violations.append("The final physical cards violate the Required/Forbidden Card declaration.")
            if variations.enabled(Variation.TWO_OPERATIONS):
                parsed = next(
                    expression
                    for expression in parse_interpretations(solution)
                    if expression.display() == result.expression
                )
                if sum(symbol in {"u", "n", "-", "'"} for symbol in parsed.written_symbols()) < 2:
                    violations.append("Two Operations requires at least two operation symbols in the Set-Name.")
            answers.append(
                CheckedAnswer(
                    restriction_display,
                    result,
                    active.ids,
                    tuple(violations),
                )
            )
            if len(answers) > max_interpretations:
                raise ValueError(f"Answer has more than {max_interpretations} legal interpretations.")
    unique = {
        (answer.restriction, answer.solution.expression, answer.solution.cards, answer.violations): answer
        for answer in answers
    }
    return tuple(unique[key] for key in sorted(unique, key=lambda item: (item[0] or "", item[1], item[2], item[3])))
