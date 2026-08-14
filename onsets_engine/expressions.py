"""Set-Name parser, interpretation enumerator, and evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Sequence

from .models import EvaluationStep, InterpretationResult, Universe, Variation, VariationConfig
from .notation import display_symbol, normalize_expression


@dataclass(frozen=True, slots=True)
class Expr:
    kind: str
    symbol: str = ""
    left: "Expr | None" = None
    right: "Expr | None" = None

    @classmethod
    def atom(cls, symbol: str) -> "Expr":
        return cls("atom", symbol)

    @classmethod
    def complement(cls, child: "Expr") -> "Expr":
        return cls("prime", "'", child)

    @classmethod
    def binary(cls, symbol: str, left: "Expr", right: "Expr") -> "Expr":
        return cls("binary", symbol, left, right)

    def display(self) -> str:
        if self.kind == "atom":
            return self.symbol
        if self.kind == "prime":
            assert self.left is not None
            child = self.left.display()
            return f"{child}'"
        assert self.left is not None and self.right is not None
        return f"({self.left.display()} {display_symbol(self.symbol)} {self.right.display()})"

    def written_symbols(self) -> tuple[str, ...]:
        if self.kind == "atom":
            return (self.symbol,)
        if self.kind == "prime":
            assert self.left is not None
            return self.left.written_symbols() + ("'",)
        assert self.left is not None and self.right is not None
        return self.left.written_symbols() + (self.symbol,) + self.right.written_symbols()


class ExpressionParser:
    def __init__(self, text: str, *, max_interpretations: int = 1_000):
        if max_interpretations < 1:
            raise ValueError("max_interpretations must be positive.")
        self.text = normalize_expression(text)
        self.index = 0
        self.max_interpretations = max_interpretations

    def parse(self) -> tuple[Expr, ...]:
        expressions = self._sequence(stop_at_close=False)
        if self.index != len(self.text):
            raise ValueError(f"Unexpected symbol at position {self.index + 1}.")
        unique = {expr.display(): expr for expr in expressions}
        return tuple(unique[key] for key in sorted(unique))

    def _sequence(self, *, stop_at_close: bool) -> tuple[Expr, ...]:
        terms: list[tuple[Expr, ...]] = [self._term()]
        operators: list[str] = []
        while self.index < len(self.text):
            symbol = self.text[self.index]
            if symbol == ")":
                if stop_at_close:
                    break
                raise ValueError("Closing parenthesis has no matching opening parenthesis.")
            if symbol in {"c", "="}:
                raise ValueError("Restriction operators are not valid inside a Set-Name.")
            if symbol not in {"u", "n", "-"}:
                raise ValueError(f"Expected a binary operation at position {self.index + 1}.")
            operators.append(symbol)
            self.index += 1
            terms.append(self._term())

        output: list[Expr] = []
        for selected in product(*terms):
            output.extend(_binary_trees(selected, tuple(operators)))
            if len(output) > self.max_interpretations:
                raise ValueError(
                    f"Expression has more than {self.max_interpretations} legal interpretations."
                )
        return tuple(output)

    def _term(self) -> tuple[Expr, ...]:
        if self.index >= len(self.text):
            raise ValueError("Expression cannot end with a binary operation.")
        symbol = self.text[self.index]
        if symbol in "BRGYVZ":
            nodes = (Expr.atom(symbol),)
            self.index += 1
        elif symbol == "(":
            self.index += 1
            if self.index < len(self.text) and self.text[self.index] == ")":
                raise ValueError("Grouping symbols cannot be empty.")
            nodes = self._sequence(stop_at_close=True)
            if self.index >= len(self.text) or self.text[self.index] != ")":
                raise ValueError("Opening parenthesis has no matching closing parenthesis.")
            self.index += 1
        elif symbol == "'":
            raise ValueError("Complement must follow a set or grouped expression.")
        else:
            raise ValueError(f"Expected a set at position {self.index + 1}.")
        while self.index < len(self.text) and self.text[self.index] == "'":
            nodes = tuple(Expr.complement(node) for node in nodes)
            self.index += 1
        return nodes


def _binary_trees(terms: Sequence[Expr], operators: Sequence[str]) -> tuple[Expr, ...]:
    if not operators:
        return (terms[0],)
    trees: list[Expr] = []
    for split, operator in enumerate(operators):
        lefts = _binary_trees(terms[: split + 1], operators[:split])
        rights = _binary_trees(terms[split + 1 :], operators[split + 1 :])
        for left, right in product(lefts, rights):
            trees.append(Expr.binary(operator, left, right))
    return tuple(trees)


def parse_interpretations(text: str, *, max_interpretations: int = 1_000) -> tuple[Expr, ...]:
    return ExpressionParser(text, max_interpretations=max_interpretations).parse()


def evaluate(expr: Expr, universe: Universe, variations: VariationConfig = VariationConfig()) -> tuple[frozenset[str], tuple[EvaluationStep, ...]]:
    all_cards = frozenset(universe.ids)
    order = {card_id: index for index, card_id in enumerate(universe.ids)}
    steps: list[EvaluationStep] = []

    def visit(node: Expr) -> frozenset[str]:
        if node.kind == "atom":
            if node.symbol == "V":
                result = all_cards
            elif node.symbol == "Z":
                result = frozenset()
            else:
                result = frozenset(
                    card.card_id for card in universe.cards if node.symbol in card.dots
                )
            steps.append(EvaluationStep(node.display(), _ordered(result, order), f"Name the {node.symbol} set."))
            return result
        assert node.left is not None
        left = visit(node.left)
        if node.kind == "prime":
            result = all_cards - left
            steps.append(EvaluationStep(node.display(), _ordered(result, order), "Take the complement in the active Universe."))
            return result
        assert node.right is not None
        right = visit(node.right)
        if node.symbol == "u":
            result = left | right
            explanation = "Take the union."
        elif node.symbol == "n":
            result = left & right
            explanation = "Take the intersection."
        elif variations.enabled(Variation.SYMMETRIC_DIFFERENCE):
            result = left ^ right
            explanation = "Take the symmetric difference."
        else:
            result = left - right
            explanation = "Subtract the right set from the left set."
        steps.append(EvaluationStep(node.display(), _ordered(result, order), explanation))
        return frozenset(result)

    return visit(expr), tuple(steps)


def _ordered(cards: Iterable[str], order: dict[str, int]) -> tuple[str, ...]:
    return tuple(sorted(cards, key=order.__getitem__))


def double_set_cards(universe: Universe, variations: VariationConfig) -> frozenset[str]:
    expression = variations.double_set_expression
    if not expression:
        return frozenset()
    double_variations = VariationConfig(
        active=(
            frozenset({Variation.SYMMETRIC_DIFFERENCE})
            if variations.double_set_uses_symmetric_difference
            else frozenset()
        )
    )
    interpretations = parse_interpretations(expression)
    if len(interpretations) != 1:
        raise ValueError("The Double Set declaration must have one unambiguous interpretation.")
    cards, _ = evaluate(interpretations[0], universe, double_variations)
    return cards


def weighted_value(cards: Iterable[str], universe: Universe, variations: VariationConfig) -> int:
    physical = frozenset(cards)
    doubled = double_set_cards(universe, variations)
    return len(physical) + len(physical & doubled)


def enumerate_evaluations(
    text: str,
    universe: Universe,
    variations: VariationConfig = VariationConfig(),
    *,
    max_interpretations: int = 1_000,
    weight_universe: Universe | None = None,
) -> tuple[InterpretationResult, ...]:
    results = []
    for expression in parse_interpretations(text, max_interpretations=max_interpretations):
        cards, steps = evaluate(expression, universe, variations)
        results.append(
            InterpretationResult(
                expression.display(),
                tuple(card_id for card_id in universe.ids if card_id in cards),
                weighted_value(cards, weight_universe or universe, variations),
                steps,
            )
        )
    return tuple(results)
