"""Versioned request and response schemas for the web client."""

from __future__ import annotations

from pydantic import BaseModel, Field

from onsets_engine import Division, Situation, Variation


class VariationPayload(BaseModel):
    active: list[Variation] = Field(default_factory=list)
    wild_cube: str | None = None
    wild_cube_section: str | None = None
    wild_cube_ordinal: int | None = Field(default=None, ge=1)
    wild_as: str | None = None
    blank_dots: list[str] = Field(default_factory=list)
    blank_card_auto: bool = False
    double_set_expression: str | None = None
    double_set_uses_symmetric_difference: bool = False
    required_card: str | None = None
    forbidden_card: str | None = None


class CheckRequest(BaseModel):
    universe: list[str]
    division: Division = Division.CUSTOM
    solution: str = ""
    restriction: str = ""
    variations: VariationPayload = Field(default_factory=VariationPayload)
    max_interpretations: int = Field(default=1_000, ge=1, le=5_000)
    proceed_anyway: bool = False


class SolveRequest(BaseModel):
    universe: list[str]
    division: Division = Division.CUSTOM
    situation: Situation = Situation.IMPOSSIBLE
    goal: int = Field(ge=0)
    required: str = ""
    permitted: str = ""
    forbidden: str = ""
    resources: str = ""
    variations: VariationPayload = Field(default_factory=VariationPayload)
    requested: int = Field(default=5, ge=1, le=100)
    time_limit_seconds: float = Field(default=5.0, gt=0, le=60)
    max_solution_cubes: int | None = Field(default=None, ge=2, le=20)
    max_restriction_cubes: int | None = Field(default=None, ge=3, le=24)
    proceed_anyway: bool = False
