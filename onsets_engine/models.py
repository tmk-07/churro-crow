"""Immutable domain models for the On-Sets calculation engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


RULESET_ID = "agloa-2026-27"
COLORS = ("B", "R", "G", "Y")
SET_SYMBOLS = ("B", "R", "G", "Y", "V", "Z")
SET_OPERATIONS = ("u", "n", "-", "'")
RESTRICTION_OPERATIONS = ("c", "=")
CUBE_SYMBOLS = SET_SYMBOLS + SET_OPERATIONS + RESTRICTION_OPERATIONS

CARD_ORDER = (
    "BR", "BRY", "BY", "B",
    "BRG", "BRGY", "BGY", "BG",
    "RG", "RGY", "GY", "G",
    "R", "RY", "Y", "blank",
)


class Division(str, Enum):
    ELEMENTARY = "elementary"
    MIDDLE = "middle"
    JUNIOR = "junior"
    SENIOR = "senior"
    CUSTOM = "custom"


class Situation(str, Enum):
    NOW = "now"
    IMPOSSIBLE = "impossible"
    FORCEOUT = "forceout"


class Variation(str, Enum):
    NO_NULL = "no_null"
    SYMMETRIC_DIFFERENCE = "symmetric_difference"
    MULTIPLE_OPERATIONS = "multiple_operations"
    TWO_OPERATIONS = "two_operations"
    UNION_INTERSECTION_INTERCHANGEABLE = "union_intersection_interchangeable"
    UNIVERSE_NULL_INTERCHANGEABLE = "universe_null_interchangeable"
    WILD_CUBE = "wild_cube"
    BLANK_CARD_WILD = "blank_card_wild"
    DOUBLE_SET = "double_set"
    REQUIRED_FORBIDDEN_CARD = "required_forbidden_card"


@dataclass(frozen=True, slots=True)
class Card:
    card_id: str
    dots: frozenset[str]


@dataclass(frozen=True, slots=True)
class Universe:
    cards: tuple[Card, ...]

    def __post_init__(self) -> None:
        ids = [card.card_id for card in self.cards]
        if len(ids) != len(set(ids)):
            raise ValueError("A Universe cannot contain duplicate physical cards.")
        unknown = set(ids) - set(CARD_ORDER)
        if unknown:
            raise ValueError(f"Unknown On-Sets cards: {', '.join(sorted(unknown))}.")

    @classmethod
    def from_ids(
        cls,
        card_ids: Iterable[str],
        *,
        blank_dots: Iterable[str] = (),
    ) -> "Universe":
        selected = set(card_ids)
        blank = frozenset(color.upper() for color in blank_dots)
        if not blank <= set(COLORS):
            raise ValueError("Blank Card Wild colors must be B, R, G, or Y.")
        cards = []
        for card_id in CARD_ORDER:
            if card_id not in selected:
                continue
            dots = blank if card_id == "blank" else frozenset(card_id)
            cards.append(Card(card_id, dots))
        return cls(tuple(cards))

    @classmethod
    def full(cls) -> "Universe":
        return cls.from_ids(CARD_ORDER)

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(card.card_id for card in self.cards)

    def dots_for(self, card_id: str) -> frozenset[str]:
        for card in self.cards:
            if card.card_id == card_id:
                return card.dots
        raise KeyError(card_id)

    def restrict_to(self, card_ids: Iterable[str]) -> "Universe":
        keep = set(card_ids)
        return Universe(tuple(card for card in self.cards if card.card_id in keep))


@dataclass(frozen=True, slots=True)
class CubeInventory:
    """Hashable multiset of the symbols currently showing on physical cubes."""

    items: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        previous = ""
        for symbol, count in self.items:
            if symbol not in CUBE_SYMBOLS:
                raise ValueError(f"Unknown cube symbol: {symbol}.")
            if count <= 0:
                raise ValueError("Cube counts must be positive.")
            if previous and symbol <= previous:
                raise ValueError("CubeInventory items must be unique and sorted.")
            previous = symbol

    @classmethod
    def from_mapping(cls, counts: Mapping[str, int]) -> "CubeInventory":
        return cls(tuple(sorted((symbol, int(count)) for symbol, count in counts.items() if count)))

    @classmethod
    def parse(cls, text: str) -> "CubeInventory":
        from .notation import normalize_cube_text

        counts: dict[str, int] = {}
        for symbol in normalize_cube_text(text):
            counts[symbol] = counts.get(symbol, 0) + 1
        return cls.from_mapping(counts)

    def count(self, symbol: str) -> int:
        return dict(self.items).get(symbol, 0)

    @property
    def total(self) -> int:
        return sum(count for _, count in self.items)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(symbol for symbol, _ in self.items)

    def as_dict(self) -> dict[str, int]:
        return dict(self.items)

    def __add__(self, other: "CubeInventory") -> "CubeInventory":
        counts = self.as_dict()
        for symbol, count in other.items:
            counts[symbol] = counts.get(symbol, 0) + count
        return CubeInventory.from_mapping(counts)

    def contains(self, other: "CubeInventory") -> bool:
        return all(self.count(symbol) >= count for symbol, count in other.items)

    def without(self, symbols: Iterable[str]) -> "CubeInventory":
        omitted = set(symbols)
        return CubeInventory(tuple(item for item in self.items if item[0] not in omitted))


@dataclass(frozen=True, slots=True)
class VariationConfig:
    active: frozenset[Variation] = frozenset()
    wild_cube: str | None = None
    wild_cube_section: str | None = None
    wild_cube_ordinal: int | None = None
    wild_as: str | None = None
    blank_dots: frozenset[str] = frozenset()
    blank_card_auto: bool = False
    double_set_expression: str | None = None
    double_set_uses_symmetric_difference: bool = False
    required_card: str | None = None
    forbidden_card: str | None = None

    def enabled(self, variation: Variation) -> bool:
        return variation in self.active

    @property
    def wild_cube_id(self) -> str | None:
        if not self.wild_cube:
            return None
        section = self.wild_cube_section or "resources"
        ordinal = self.wild_cube_ordinal or 1
        return f"{section}:{self.wild_cube}:{ordinal}"


@dataclass(frozen=True, slots=True)
class GameState:
    universe: Universe
    goal: int
    division: Division
    situation: Situation
    required: CubeInventory = CubeInventory()
    permitted: CubeInventory = CubeInventory()
    forbidden: CubeInventory = CubeInventory()
    resources: CubeInventory = CubeInventory()
    variations: VariationConfig = VariationConfig()
    ruleset_id: str = RULESET_ID

    def __post_init__(self) -> None:
        if self.goal < 0:
            raise ValueError("The numeric Goal cannot be negative.")
        if self.ruleset_id != RULESET_ID:
            raise ValueError(f"Unsupported ruleset: {self.ruleset_id}.")


@dataclass(frozen=True, slots=True)
class EvaluationStep:
    expression: str
    cards: tuple[str, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class InterpretationResult:
    expression: str
    cards: tuple[str, ...]
    value: int
    steps: tuple[EvaluationStep, ...] = ()


@dataclass(frozen=True, slots=True)
class RestrictionResult:
    expression: str
    remaining_cards: tuple[str, ...]
    removed_cards: tuple[str, ...]
    link_removals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CheckedAnswer:
    restriction: str | None
    solution: InterpretationResult
    restricted_universe: tuple[str, ...]
    violations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CubeUse:
    written: CubeInventory
    physical: CubeInventory
    resource_cubes: int
    resource_inventory: CubeInventory = CubeInventory()
    ordinary_resource_inventory: CubeInventory = CubeInventory()
    wild_cube_used: bool = False
    wild_cube_id: str | None = None
    wild_cube_as: str | None = None
    wild_cube_from_resources: bool = False
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SolverAnswer:
    solution: str
    cards: tuple[str, ...]
    value: int
    cube_use: CubeUse
    restriction: str | None = None
    restriction_cube_use: CubeUse | None = None
    variation_notes: tuple[str, ...] = ()
    steps: tuple[EvaluationStep, ...] = ()
    doubled_cards: tuple[str, ...] = ()

    @property
    def cube_count(self) -> int:
        count = self.cube_use.written.total
        if self.restriction_cube_use:
            count += self.restriction_cube_use.written.total
        return count

    @property
    def resource_inventory(self) -> CubeInventory:
        if self.restriction_cube_use is None:
            return self.cube_use.resource_inventory
        combined = {
            symbol: max(
                self.cube_use.ordinary_resource_inventory.count(symbol),
                self.restriction_cube_use.ordinary_resource_inventory.count(symbol),
            )
            for symbol in set(self.cube_use.ordinary_resource_inventory.symbols)
            | set(self.restriction_cube_use.ordinary_resource_inventory.symbols)
        }
        wild_use = next(
            (
                use
                for use in (self.cube_use, self.restriction_cube_use)
                if use.wild_cube_from_resources and use.wild_cube_id
            ),
            None,
        )
        if wild_use:
            face = wild_use.wild_cube_id.split(":", 2)[1]
            combined[face] = combined.get(face, 0) + 1
        if not combined:
            # Compatibility for callers that construct CubeUse directly.
            combined = {
                symbol: max(
                    self.cube_use.resource_inventory.count(symbol),
                    self.restriction_cube_use.resource_inventory.count(symbol),
                )
                for symbol in set(self.cube_use.resource_inventory.symbols)
                | set(self.restriction_cube_use.resource_inventory.symbols)
            }
        return CubeInventory.from_mapping(combined)


@dataclass(frozen=True, slots=True)
class SolutionGroup:
    cards: tuple[str, ...]
    value: int
    answers: tuple[SolverAnswer, ...]


@dataclass(frozen=True, slots=True)
class SolverReport:
    groups: tuple[SolutionGroup, ...]
    requested: int
    returned: int
    search_complete: bool
    elapsed_seconds: float
    warnings: tuple[str, ...] = ()
