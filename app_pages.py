"""Streamlit page renderers for the Phase 4 application."""

from __future__ import annotations

import streamlit as st

from leaderboard_store import LeaderboardConfigurationError, read_scores
from onsets_engine import (
    CubeInventory,
    GameState,
    Situation,
    check_expression,
    enumerate_restriction_sets,
    apply_restrictions,
    solve,
    validate_game_state,
)
from onsets_engine.notation import display_cube_inventory
from ui_shared import cards_text, cube_trays, division_selector, universe_selector, variation_controls
from z_leaderboard import _top_scores, MODES


def learn_page() -> None:
    st.title("Churro Crow")
    st.write("A private On-Sets checker and solver for learning, practice, and real game situations.")
    st.info("Ruleset: AGLOA 2026–27. Practice drills are intentionally deferred while the checker and solver are rebuilt.")

    basics, notation, workflow = st.columns(3)
    with basics:
        st.subheader("1 · Build a Universe")
        st.write("Choose the physical cards dealt for the shake. A color names every selected card carrying that dot.")
    with notation:
        st.subheader("2 · Write Set-Names")
        st.write("Use `U`, `∩`, `−`, and `'`. Grouping is applied first; complement has priority.")
    with workflow:
        st.subheader("3 · Check or Solve")
        st.write("Check lists every legal interpretation. Solve uses the actual Required, Permitted, Forbidden, and Resource cubes.")

    st.subheader("Core notation")
    st.table(
        {
            "Meaning": ["Universe", "Null set", "Union", "Intersection", "Set subtraction", "Complement", "Subset restriction", "Equals restriction"],
            "Write": ["V", "Z", "U", "∩ or n", "− or -", "'", "⊂ or c", "="],
            "Example": ["V", "Z", "B U R", "G ∩ Y", "B − R", "G'", "B ⊂ R", "G = Y"],
        }
    )

    st.subheader("How ambiguity works")
    st.write("Binary operations have no relative priority. Therefore `B U G − R` has two legal interpretations:")
    st.code("((B U G) − R)\n(B U (G − R))")
    st.write("A tournament Solution is valid only when every legal interpretation equals the Goal. Generated Solutions include enough parentheses to avoid that ambiguity.")

    st.subheader("Solver situations")
    st.markdown(
        """
        - **Now:** Required + any Permitted + at most one actual Resource cube.
        - **Impossible:** Required + any Permitted + any of the actual remaining Resource cubes.
        - **Forceout:** the last Resource cube has already moved to Required or Permitted, so Resources is empty.
        """
    )


def check_page() -> None:
    st.title("Check an expression")
    st.write("See every legal parenthesized interpretation and the physical cards each one names.")
    top = st.columns([1, 2])
    with top[0]:
        division = division_selector(key="check")
    with top[1]:
        card_ids = universe_selector(division, key="check")

    # The checker has no game-state cube validation, but the shake-cube input
    # lets Wild Cube and No Null declarations be checked for effect.
    resources_text = st.text_input(
        "Shake cubes (only needed to declare Wild Cube or No Null)",
        key="check_resources",
        placeholder="Example: BGu'",
    )
    try:
        resources = CubeInventory.parse(resources_text)
    except ValueError as exc:
        st.error(str(exc))
        resources = CubeInventory()
    universe, variations, variation_issues = variation_controls(
        division, card_ids, {"shake": resources}, key="check"
    )
    for issue in variation_issues:
        st.warning(issue)
    proceed = not variation_issues or st.checkbox("Proceed anyway", key="check_proceed")

    expressions = st.columns(2)
    with expressions[0]:
        restriction = st.text_area(
            "Restriction(s), optional",
            placeholder="One per line, or separate with commas: B ⊂ R",
            key="check_restriction",
        )
    with expressions[1]:
        solution = st.text_input(
            "Set-Name, optional",
            placeholder="Example: B U G − R",
            key="check_solution",
        )
        goal_text = st.text_input(
            "Goal, optional",
            placeholder="Example: 6",
            key="check_goal",
        )

    if st.button("Check expression", type="primary", use_container_width=True, key="check_run"):
        if not proceed:
            st.error("Resolve the variation declaration or select Proceed anyway.")
            return
        if not restriction.strip() and not solution.strip():
            st.error("Enter a Restriction, a Set-Name, or both.")
            return
        try:
            goal = int(goal_text) if goal_text.strip() else None
            if goal is not None and goal < 0:
                raise ValueError("Goal cannot be negative.")
            if restriction.strip() and not solution.strip():
                combinations = enumerate_restriction_sets(restriction)
                for index, restrictions in enumerate(combinations, 1):
                    active, details = apply_restrictions(restrictions, universe, variations)
                    st.subheader(f"Restriction interpretation {index}")
                    for detail in details:
                        st.code(detail.expression)
                        st.write(f"Removed: {cards_text(detail.removed_cards)}")
                    st.metric("Remaining Universe", len(active.ids))
                    st.write(cards_text(active.ids))
                return
            answers = check_expression(
                universe,
                solution,
                restriction_text=restriction,
                variations=variations,
            )
        except ValueError as exc:
            st.error(str(exc))
            return

        if not answers:
            st.error("No legal interpretation satisfies the active restrictions and variations.")
            return
        values = {answer.solution.value for answer in answers}
        if goal is not None:
            if values == {goal} and not any(answer.violations for answer in answers):
                st.success(f"Every legal interpretation equals the Goal of {goal}.")
            else:
                st.error(f"This is not tournament-valid for Goal {goal}; at least one interpretation has a wrong value or violates an active variation.")
        st.caption(f"{len(answers)} legal interpretation{'s' if len(answers) != 1 else ''}")
        for index, answer in enumerate(answers, 1):
            with st.container(border=True):
                st.subheader(f"Interpretation {index}")
                if answer.restriction:
                    st.write("Restriction")
                    st.code(answer.restriction)
                    if answer.restriction_cube_use:
                        st.caption(
                            "Restriction cubes — written: "
                            f"{display_cube_inventory(answer.restriction_cube_use.written.items)}; "
                            "physical: "
                            f"{display_cube_inventory(answer.restriction_cube_use.physical.items)}"
                        )
                    st.caption(f"Restricted Universe: {cards_text(answer.restricted_universe)}")
                st.code(answer.solution.expression)
                value_col, card_col = st.columns([1, 4])
                value_col.metric("Value", answer.solution.value)
                card_col.write("Physical cards")
                card_col.write(cards_text(answer.solution.cards))
                for violation in answer.violations:
                    st.warning(violation)
                if goal is not None:
                    (st.success if answer.solution.value == goal else st.warning)(
                        f"This interpretation {'equals' if answer.solution.value == goal else 'does not equal'} {goal}."
                    )
                with st.expander("Evaluation steps"):
                    for step in answer.solution.steps:
                        st.write(f"`{step.expression}` — {step.explanation} {cards_text(step.cards)}")


def _situation_selector() -> Situation:
    labels = {
        Situation.NOW: "Now — at most one Resource cube",
        Situation.IMPOSSIBLE: "Impossible — any actual Resource cubes",
        Situation.FORCEOUT: "Forceout — no Resource cubes remain",
    }
    return st.radio(
        "Solution-writing context",
        tuple(Situation),
        format_func=labels.__getitem__,
        horizontal=True,
        key="solve_situation",
    )


def solve_page() -> None:
    st.title("Find Solutions")
    st.write("Describe the current shake. Results are grouped by the physical card set they contain, with different card sets shown first.")
    settings = st.columns([1, 2, 1])
    with settings[0]:
        division = division_selector(key="solve")
    with settings[1]:
        situation = _situation_selector()
    with settings[2]:
        goal = st.number_input("Numeric Goal", min_value=0, step=1, value=6, key="solve_goal")

    card_ids = universe_selector(division, key="solve")
    try:
        required, permitted, forbidden, resources = cube_trays(key="solve")
    except ValueError as exc:
        st.error(str(exc))
        return

    universe, variations, variation_issues = variation_controls(
        division,
        card_ids,
        {
            "required": required,
            "permitted": permitted,
            "forbidden": forbidden,
            "resources": resources,
        },
        key="solve",
        solver_mode=True,
    )
    for issue in variation_issues:
        st.warning(issue)
    proceed = not variation_issues or st.checkbox("Proceed anyway", key="solve_proceed")

    controls = st.columns(3)
    with controls[0]:
        requested = int(st.number_input("Solutions wanted", min_value=1, max_value=100, value=5, step=1, key="solve_requested"))
    with controls[1]:
        time_limit = float(st.number_input("Interactive search limit (seconds)", min_value=1.0, max_value=60.0, value=5.0, step=1.0, key="solve_time_limit"))
    with controls[2]:
        st.write("")
        st.write("")
        run = st.button("Generate Solutions", type="primary", use_container_width=True, key="solve_run")
    run = run or bool(st.session_state.pop("solve_auto_run", False))

    if run:
        if not card_ids:
            st.error("Select at least one Universe card.")
            return
        if not proceed:
            st.error("Resolve the variation declaration or select Proceed anyway.")
            return
        state = GameState(
            universe=universe,
            goal=int(goal),
            division=division,
            situation=situation,
            required=required,
            permitted=permitted,
            forbidden=forbidden,
            resources=resources,
            variations=variations,
        )
        state_errors, state_warnings = validate_game_state(state)
        for warning in state_warnings:
            st.warning(warning)
        if state_errors:
            for error in state_errors:
                st.error(error)
            return
        with st.spinner("Searching shortest valid expressions first…"):
            report = solve(state, requested=requested, time_limit_seconds=time_limit)
        st.session_state["solve_report"] = report

    report = st.session_state.get("solve_report")
    if report is None:
        return
    for warning in report.warnings:
        st.info(warning)
    result_cols = st.columns(3)
    result_cols[0].metric("Solutions", report.returned)
    result_cols[1].metric("Different card sets", len(report.groups))
    result_cols[2].metric("Search time", f"{report.elapsed_seconds:.2f}s")
    if not report.groups:
        if "Nothing was found." not in report.warnings:
            st.warning("Nothing was found.")
        return

    for group_index, group in enumerate(report.groups, 1):
        st.markdown(f"<div class='cc-cardset'><strong>Card set {group_index}</strong><br>{cards_text(group.cards)}<br>Goal value: {group.value}</div>", unsafe_allow_html=True)
        for answer_index, answer in enumerate(group.answers, 1):
            with st.container(border=True):
                st.write(f"**Solution {answer_index} for this card set**")
                if answer.restriction:
                    st.write("Restriction")
                    st.code(answer.restriction)
                st.write("Set-Name")
                st.code(answer.solution)
                use_cols = st.columns(3)
                use_cols[0].write(f"Written cubes: {display_cube_inventory(answer.cube_use.written.items)}")
                use_cols[1].write(f"Physical cubes: {display_cube_inventory(answer.cube_use.physical.items)}")
                use_cols[2].write(
                    "Resource cubes used: "
                    f"{display_cube_inventory(answer.resource_inventory.items)}"
                )
                if answer.variation_notes:
                    st.caption(" · ".join(answer.variation_notes))
                with st.expander("Evaluation steps"):
                    for step in answer.steps:
                        st.write(f"`{step.expression}` — {step.explanation} {cards_text(step.cards)}")

    def request_more() -> None:
        st.session_state["solve_requested"] = min(
            100, int(st.session_state.get("solve_requested", 5)) + 5
        )
        st.session_state.pop("solve_report", None)
        st.session_state["solve_auto_run"] = True

    st.button("Find 5 more", key="solve_more", on_click=request_more)


def practice_page() -> None:
    st.title("Practice")
    st.info("Practice is under construction and will be rebuilt after the checker and solver are reviewed.")
    st.write("Planned drills include padding, Restrictions, and timed Solution finding. Existing public leaderboard data remains available from the Leaderboards page.")


def leaderboard_page() -> None:
    st.title("Leaderboards")
    st.caption("Existing public practice rankings")
    columns = st.columns(3)
    for column, (mode, title) in zip(columns, MODES.items()):
        with column:
            st.subheader(title)
            try:
                scores = read_scores(mode)
            except LeaderboardConfigurationError as exc:
                st.info(str(exc))
            except Exception:
                st.error("The leaderboard is temporarily unavailable.")
            else:
                if scores:
                    st.dataframe(_top_scores(scores), hide_index=True, use_container_width=True)
                else:
                    st.info("No scores yet")
