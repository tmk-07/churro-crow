"""Reusable Streamlit controls. This module contains presentation, not game logic."""

from __future__ import annotations

from pathlib import Path
from typing import AbstractSet, Mapping

import streamlit as st

from onsets_engine import (
    AUTOMATIC_VARIATIONS,
    AVAILABLE_VARIATIONS,
    CARD_ORDER,
    CubeInventory,
    Division,
    Universe,
    Variation,
    VariationConfig,
    universe_size_warning,
    validate_variations,
)
from onsets_engine.notation import display_cube_inventory


VARIATION_LABELS = {
    Variation.NO_NULL: "No Null Restrictions",
    Variation.SYMMETRIC_DIFFERENCE: "Symmetric Difference",
    Variation.MULTIPLE_OPERATIONS: "Multiple Operations",
    Variation.TWO_OPERATIONS: "Two Operations",
    Variation.UNION_INTERSECTION_INTERCHANGEABLE: "U and ∩ Interchangeable",
    Variation.UNIVERSE_NULL_INTERCHANGEABLE: "V and Z Interchangeable",
    Variation.WILD_CUBE: "Wild Cube",
    Variation.BLANK_CARD_WILD: "Blank Card Wild",
    Variation.DOUBLE_SET: "Double Set",
    Variation.REQUIRED_FORBIDDEN_CARD: "Required/Forbidden Card",
}


def app_chrome() -> None:
    st.set_page_config(
        page_title="Churro Crow · On-Sets Tools",
        page_icon="🟦",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {max-width: 1240px; padding-top: 2rem;}
        [data-testid="stMetric"] {background: color-mix(in srgb, var(--primary-color) 8%, transparent); padding: .75rem; border-radius: .65rem;}
        .cc-cardset {border-left: 4px solid var(--primary-color); padding: .25rem .8rem; margin: .3rem 0 1rem;}
        code {font-size: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def division_selector(*, key: str) -> Division:
    labels = {
        Division.ELEMENTARY: "Elementary",
        Division.MIDDLE: "Middle",
        Division.JUNIOR: "Junior",
        Division.SENIOR: "Senior",
        Division.CUSTOM: "Custom Practice",
    }
    selected = st.selectbox(
        "Division",
        tuple(Division),
        format_func=labels.__getitem__,
        key=f"{key}_division",
        help="Division controls the tournament Universe warning and available variations.",
    )
    return selected


def card_grid_selector(division: Division, *, key: str) -> tuple[str, ...]:
    """Compact 4×4 physical-card picker matching the On-Sets chart."""

    state_key = f"{key}_card_states"
    if state_key not in st.session_state:
        st.session_state[state_key] = {card_id: True for card_id in CARD_ORDER}
    states = st.session_state[state_key]
    for card_id in CARD_ORDER:
        states.setdefault(card_id, True)

    st.subheader("Universe cards")
    st.caption("Click a card label to include or exclude that physical card.")
    columns = st.columns(4, gap="small")
    asset_root = Path(__file__).resolve().parent / "Onsets Cards"
    for index, card_id in enumerate(CARD_ORDER):
        with columns[index % 4]:
            st.image(str(asset_root / f"{card_id}.png"), width=92)
            included = bool(states[card_id])
            if st.button(
                f"{'✓' if included else '○'} {card_id}",
                key=f"{key}_card_toggle_{card_id}",
                type="primary" if included else "secondary",
                use_container_width=True,
            ):
                states[card_id] = not included
                st.rerun()

    selected = tuple(card_id for card_id in CARD_ORDER if states[card_id])
    st.caption(f"{len(selected)} of 16 cards selected")
    warning = universe_size_warning(division, len(selected))
    if warning:
        st.warning(warning)
    if not selected:
        st.error("Select at least one physical card.")
    return selected


def cube_trays(*, key: str) -> tuple[CubeInventory, CubeInventory, CubeInventory, CubeInventory]:
    st.subheader("Current cube state")
    st.caption("Enter the symbols showing on the physical cubes. Repeated characters represent repeated cubes. Keyboard aliases are accepted.")
    columns = st.columns(4)
    labels = (
        ("Required", "BRu", "Every cube here must be used."),
        ("Permitted", "GY'", "Any subset may be used."),
        ("Forbidden", "", "These cubes cannot be used."),
        ("Resources", "-c", "Availability depends on Now, Impossible, or Forceout."),
    )
    values = []
    for column, (label, placeholder, help_text) in zip(columns, labels):
        with column:
            values.append(
                st.text_input(
                    label,
                    placeholder=placeholder,
                    help=help_text,
                    key=f"{key}_{label.casefold()}",
                )
            )
    inventories = tuple(CubeInventory.parse(value) for value in values)
    for column, inventory in zip(columns, inventories):
        with column:
            st.caption(display_cube_inventory(inventory.items))
    return inventories  # type: ignore[return-value]


def variation_controls(
    division: Division,
    card_ids: tuple[str, ...],
    cube_sections: Mapping[str, CubeInventory],
    *,
    key: str,
    solver_mode: bool = False,
    expression_only: bool = False,
) -> tuple[Universe, VariationConfig, tuple[str, ...]]:
    st.subheader("Variations")
    if expression_only:
        st.caption("Only variations that can change the expression's cards, value, or legality are shown.")
    else:
        st.caption("Automatic division rules are already enabled. Illegal private-practice declarations produce a warning and can be used with Proceed anyway.")
    available = AVAILABLE_VARIATIONS[division] | AUTOMATIC_VARIATIONS[division]
    if expression_only:
        available -= {
            Variation.WILD_CUBE,
            Variation.MULTIPLE_OPERATIONS,
            Variation.UNION_INTERSECTION_INTERCHANGEABLE,
            Variation.UNIVERSE_NULL_INTERCHANGEABLE,
        }
    automatic = AUTOMATIC_VARIATIONS[division] & available
    selected: set[Variation] = set()
    columns = st.columns(3)
    ordered = tuple(VARIATION_LABELS)
    for index, variation in enumerate(ordered):
        if variation not in available:
            continue
        with columns[index % 3]:
            enabled = st.checkbox(
                VARIATION_LABELS[variation],
                value=variation in automatic,
                disabled=variation in automatic,
                key=f"{key}_variation_{variation.value}",
            )
            if enabled:
                selected.add(variation)
    selected.update(automatic)

    wild_cube = None
    wild_cube_section = None
    wild_cube_ordinal = None
    wild_as = None
    if Variation.WILD_CUBE in selected:
        choices = tuple(
            (section, symbol, ordinal)
            for section, inventory in cube_sections.items()
            for symbol, count in inventory.items
            for ordinal in range(1, count + 1)
        )
        section_labels = {
            "required": "Required",
            "permitted": "Permitted",
            "forbidden": "Forbidden",
            "resources": "Resources",
            "shake": "Shake",
        }
        selected_wild = st.selectbox(
            "Wild cube selected for this shake",
            (None,) + choices,
            format_func=lambda value: (
                "Choose one physical cube"
                if value is None
                else f"{section_labels.get(value[0], value[0].title())} · {value[1]} #{value[2]}"
            ),
            key=f"{key}_wild_cube",
            help="Each occurrence is a different physical cube, even when two cubes show the same symbol.",
        )
        if selected_wild is not None:
            wild_cube_section, wild_cube, wild_cube_ordinal = selected_wild
        wild_as = st.selectbox(
            "Wild interpretation",
            (None, "B", "R", "G", "Y", "V", "Z", "u", "n", "-", "'"),
            format_func=lambda value: "Let the solver choose" if value is None else value,
            key=f"{key}_wild_as",
            help="A wild cube has one consistent meaning throughout a Solution.",
        )

    blank_dots: frozenset[str] = frozenset()
    blank_card_auto = False
    if Variation.BLANK_CARD_WILD in selected:
        if solver_mode:
            blank_card_auto = st.checkbox(
                "Let the solver choose the blank card's colors",
                value=True,
                key=f"{key}_blank_auto",
            )
        if not blank_card_auto:
            blank_dots = frozenset(
                st.multiselect(
                    "Colors placed on the blank card",
                    ("B", "R", "G", "Y"),
                    key=f"{key}_blank_dots",
                )
            )

    double_set_expression = None
    double_set_symdiff = False
    if Variation.DOUBLE_SET in selected:
        double_set_expression = st.text_input(
            "Set that counts double",
            placeholder="Example: B or (R ∩ G)'",
            key=f"{key}_double_set",
        ) or None
        if Variation.SYMMETRIC_DIFFERENCE in selected:
            double_set_symdiff = st.checkbox(
                "Symmetric Difference was selected before Double Set",
                key=f"{key}_double_set_symdiff",
                help="This determines what − means inside the Double Set declaration.",
            )

    required_card = None
    forbidden_card = None
    if Variation.REQUIRED_FORBIDDEN_CARD in selected:
        card_columns = st.columns(2)
        with card_columns[0]:
            required_card = st.selectbox(
                "Required card",
                (None,) + card_ids,
                format_func=lambda value: "None" if value is None else value,
                key=f"{key}_required_card",
            )
        with card_columns[1]:
            forbidden_card = st.selectbox(
                "Forbidden card",
                (None,) + card_ids,
                format_func=lambda value: "None" if value is None else value,
                key=f"{key}_forbidden_card",
            )

    universe = Universe.from_ids(card_ids, blank_dots=blank_dots)
    config = VariationConfig(
        active=frozenset(selected),
        wild_cube=wild_cube,
        wild_cube_section=wild_cube_section,
        wild_cube_ordinal=wild_cube_ordinal,
        wild_as=wild_as,
        blank_dots=blank_dots,
        blank_card_auto=blank_card_auto,
        double_set_expression=double_set_expression,
        double_set_uses_symmetric_difference=double_set_symdiff,
        required_card=required_card,
        forbidden_card=forbidden_card,
    )
    issues = validate_variations(
        division,
        universe,
        config,
        cube_sections=cube_sections,
        validate_cube_availability=not expression_only,
    )
    return universe, config, tuple(issue.message for issue in issues)


def cards_text(
    cards: tuple[str, ...],
    doubled_cards: AbstractSet[str] = frozenset(),
) -> str:
    if not cards:
        return "no cards"
    return " · ".join(
        f"{card} (2)" if card in doubled_cards else card
        for card in cards
    )
