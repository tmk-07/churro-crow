"""Notation normalization shared by the parser, solver, and interface."""

from __future__ import annotations


ALIASES = {
    "B": "B", "b": "B", "R": "R", "r": "R",
    "G": "G", "g": "G", "Y": "Y", "y": "Y",
    "V": "V", "v": "V", "Z": "Z", "z": "Z",
    "U": "u", "u": "u", "∪": "u",
    "n": "n", "N": "n", "∩": "n",
    "-": "-", "−": "-", "–": "-",
    "'": "'", "′": "'",
    "c": "c", "C": "c", "⊂": "c", "⊆": "c",
    "=": "=", "(": "(", "[": "(", "{": "(",
    ")": ")", "]": ")", "}": ")",
}

DISPLAY = {"u": "U", "n": "∩", "-": "−", "c": "⊂"}


def normalize_expression(text: str, *, allow_empty: bool = False) -> str:
    if not isinstance(text, str):
        raise ValueError("Expression must be text.")
    compact = "".join(text.split())
    compact = compact.replace("/\\", "Z").replace("∅", "Z").replace("Ø", "Z")
    if not compact:
        if allow_empty:
            return ""
        raise ValueError("Expression cannot be empty.")
    normalized: list[str] = []
    for character in compact:
        try:
            normalized.append(ALIASES[character])
        except KeyError as exc:
            raise ValueError(f"Unknown On-Sets symbol: {character}") from exc
    return "".join(normalized)


def normalize_cube_text(text: str) -> str:
    normalized = normalize_expression(text or "", allow_empty=True)
    grouping = {"(", ")"}
    invalid = [symbol for symbol in normalized if symbol in grouping]
    if invalid:
        raise ValueError("Cube trays cannot contain grouping symbols.")
    return normalized


def display_symbol(symbol: str) -> str:
    if symbol == "Z":
        return "Z"
    return DISPLAY.get(symbol, symbol)


def display_cube_inventory(items: tuple[tuple[str, int], ...]) -> str:
    parts = []
    for symbol, count in items:
        shown = display_symbol(symbol)
        parts.append(shown if count == 1 else f"{shown}×{count}")
    return "  ".join(parts) if parts else "none"
