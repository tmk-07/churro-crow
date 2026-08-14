"""Public API for the Churro Crow On-Sets engine."""

from .checker import check_expression
from .expressions import (
    Expr,
    double_set_cards,
    enumerate_evaluations,
    evaluate,
    parse_interpretations,
    weighted_value,
)
from .models import (
    CARD_ORDER,
    RULESET_ID,
    CheckedAnswer,
    CubeInventory,
    CubeUse,
    Division,
    GameState,
    Situation,
    SolutionGroup,
    SolverAnswer,
    SolverReport,
    Universe,
    Variation,
    VariationConfig,
)
from .restrictions import (
    apply_restriction,
    apply_restrictions,
    enumerate_restriction_sets,
    no_null_satisfied_for_every_order,
    parse_restriction_interpretations,
)
from .solver import combined_resource_use_is_legal, match_cube_use, solve
from .variations import (
    AUTOMATIC_VARIATIONS,
    AVAILABLE_VARIATIONS,
    card_constraints_satisfied,
    universe_size_warning,
    validate_game_state,
    validate_variations,
    with_automatic_variations,
)

__all__ = [name for name in globals() if not name.startswith("_")]
