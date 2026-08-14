import unittest
from unittest.mock import patch
from time import monotonic

from onsets_engine import (
    CubeInventory,
    CubeUse,
    Division,
    GameState,
    Situation,
    Universe,
    Variation,
    VariationConfig,
    apply_restrictions,
    check_expression,
    combined_resource_use_is_legal,
    enumerate_evaluations,
    enumerate_restriction_sets,
    match_cube_use,
    no_null_satisfied_for_every_order,
    parse_interpretations,
    solve,
    validate_variations,
    validate_game_state,
)
from onsets_engine.solver import _independent_restriction_candidates


class ParserAndCheckerTests(unittest.TestCase):
    def setUp(self):
        self.universe = Universe.full()

    def test_official_ambiguous_example_lists_both_groupings(self):
        results = enumerate_evaluations("B U G - R", self.universe)
        self.assertEqual(
            {(item.expression, item.value) for item in results},
            {("((B U G) − R)", 6), ("(B U (G − R))", 10)},
        )

    def test_prime_and_explicit_grouping(self):
        self.assertEqual(enumerate_evaluations("R U G'", self.universe)[0].value, 12)
        self.assertEqual(enumerate_evaluations("(B U G) - R", self.universe)[0].value, 6)
        self.assertEqual(enumerate_evaluations("(B U G)'", self.universe)[0].value, 4)

    def test_malformed_expressions_are_actionable(self):
        failures = {
            "B U": "end with a binary operation",
            "B R": "Expected a binary operation",
            "(B U R": "no matching closing",
            "'B": "Complement must follow",
        }
        for expression, message in failures.items():
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(ValueError, message):
                    parse_interpretations(expression)
        with self.assertRaisesRegex(ValueError, "may not enclose"):
            enumerate_restriction_sets("(B c R)")

    def test_restrictions_are_structured_and_apply_before_solution(self):
        answers = check_expression(
            self.universe,
            "V U Z",
            restriction_text="B c R",
        )
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0].solution.value, 12)
        self.assertNotIn("B", answers[0].solution.cards)
        self.assertNotIn("BY", answers[0].solution.cards)

    def test_equals_restriction_removes_symmetric_difference(self):
        restrictions = enumerate_restriction_sets("B = R")[0]
        active, _ = apply_restrictions(restrictions, self.universe)
        expected = {
            card.card_id
            for card in self.universe.cards
            if ("B" in card.dots) == ("R" in card.dots)
        }
        self.assertEqual(set(active.ids), expected)

    def test_custom_universe_controls_v_z_and_complement(self):
        universe = Universe.from_ids(("B", "R", "BR", "blank"))
        self.assertEqual(enumerate_evaluations("V", universe)[0].value, 4)
        self.assertEqual(enumerate_evaluations("Z", universe)[0].value, 0)
        self.assertEqual(set(enumerate_evaluations("B'", universe)[0].cards), {"R", "blank"})

    def test_multiple_independent_and_chain_restrictions(self):
        independent = enumerate_restriction_sets("B c R; G = Y")[0]
        active, results = apply_restrictions(independent, self.universe)
        self.assertEqual(len(results), 2)
        self.assertLess(len(active.ids), 16)

        chain = enumerate_restriction_sets("B c R c G")[0]
        active, _ = apply_restrictions(chain, self.universe)
        expected = {
            card.card_id
            for card in self.universe.cards
            if not ("B" in card.dots and "R" not in card.dots)
            and not ("R" in card.dots and "G" not in card.dots)
        }
        self.assertEqual(set(active.ids), expected)

    def test_no_null_checks_every_independent_order(self):
        restrictions = enumerate_restriction_sets("B c R; G c Y")[0]
        config = VariationConfig(active=frozenset({Variation.NO_NULL}))
        self.assertTrue(no_null_satisfied_for_every_order(restrictions, self.universe, config))
        null = enumerate_restriction_sets("B c V")[0]
        self.assertFalse(no_null_satisfied_for_every_order(null, self.universe, config))

    def test_checker_reports_variation_violations_without_hiding_interpretations(self):
        config = VariationConfig(active=frozenset({Variation.NO_NULL, Variation.TWO_OPERATIONS}))
        answers = check_expression(
            self.universe,
            "B U Z",
            restriction_text="B c V",
            variations=config,
        )
        self.assertEqual(len(answers), 1)
        self.assertEqual(len(answers[0].violations), 2)
        self.assertTrue(any("No Null" in message for message in answers[0].violations))
        self.assertTrue(any("Two Operations" in message for message in answers[0].violations))


class VariationTests(unittest.TestCase):
    def setUp(self):
        self.universe = Universe.full()

    def test_symmetric_difference(self):
        config = VariationConfig(active=frozenset({Variation.SYMMETRIC_DIFFERENCE}))
        self.assertEqual(enumerate_evaluations("B-R", self.universe, config)[0].value, 8)

    def test_blank_card_wild_changes_membership_but_not_identity(self):
        universe = Universe.from_ids(self.universe.ids, blank_dots={"B"})
        config = VariationConfig(
            active=frozenset({Variation.BLANK_CARD_WILD}),
            blank_dots=frozenset({"B"}),
        )
        result = enumerate_evaluations("B U Z", universe, config)[0]
        self.assertEqual(result.value, 9)
        self.assertIn("blank", result.cards)

    def test_double_set_weights_without_duplicating_physical_cards(self):
        config = VariationConfig(
            active=frozenset({Variation.DOUBLE_SET}),
            double_set_expression="B",
        )
        result = enumerate_evaluations("B U Z", self.universe, config)[0]
        self.assertEqual(result.value, 16)
        self.assertEqual(len(result.cards), 8)

    def test_symmetric_difference_and_double_set_selection_order_combine(self):
        standard_double = VariationConfig(
            active=frozenset({Variation.DOUBLE_SET, Variation.SYMMETRIC_DIFFERENCE}),
            double_set_expression="B-R",
            double_set_uses_symmetric_difference=False,
        )
        symmetric_double = VariationConfig(
            active=frozenset({Variation.DOUBLE_SET, Variation.SYMMETRIC_DIFFERENCE}),
            double_set_expression="B-R",
            double_set_uses_symmetric_difference=True,
        )
        self.assertEqual(enumerate_evaluations("V U Z", self.universe, standard_double)[0].value, 20)
        self.assertEqual(enumerate_evaluations("V U Z", self.universe, symmetric_double)[0].value, 24)

    def test_blank_card_wild_combines_with_double_set(self):
        universe = Universe.from_ids(self.universe.ids, blank_dots={"B"})
        config = VariationConfig(
            active=frozenset({Variation.BLANK_CARD_WILD, Variation.DOUBLE_SET}),
            blank_dots=frozenset({"B"}),
            double_set_expression="B",
        )
        result = enumerate_evaluations("B U Z", universe, config)[0]
        self.assertEqual(len(result.cards), 9)
        self.assertEqual(result.value, 18)

    def test_interchangeable_cubes_match_the_written_math(self):
        config = VariationConfig(
            active=frozenset({Variation.UNION_INTERSECTION_INTERCHANGEABLE})
        )
        state = GameState(
            self.universe,
            12,
            Division.CUSTOM,
            Situation.FORCEOUT,
            required=CubeInventory.parse("BRn"),
            variations=config,
        )
        use = match_cube_use(("B", "u", "R"), state, state.required)
        self.assertIsNotNone(use)
        self.assertIn("Uses U/∩ interchangeable.", use.notes)

    def test_multiple_operations_can_reuse_an_operation_cube(self):
        config = VariationConfig(active=frozenset({Variation.MULTIPLE_OPERATIONS}))
        state = GameState(
            self.universe,
            0,
            Division.CUSTOM,
            Situation.FORCEOUT,
            required=CubeInventory.parse("BRu"),
            permitted=CubeInventory.parse("B"),
            variations=config,
        )
        use = match_cube_use(("B", "u", "R", "u", "B"), state, state.required)
        self.assertIsNotNone(use)
        self.assertEqual(use.physical.count("u"), 1)

    def test_wild_cube_has_one_consistent_meaning(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=1,
            wild_as="'",
        )
        state = GameState(
            self.universe,
            8,
            Division.CUSTOM,
            Situation.NOW,
            required=CubeInventory.parse("B"),
            resources=CubeInventory.parse("G"),
            variations=config,
        )
        use = match_cube_use(("B", "'"), state, state.required)
        self.assertIsNotNone(use)
        self.assertEqual(use.resource_cubes, 1)
        self.assertIn("G Wild (resources:G:1) is used as '.", use.notes)

    def test_only_the_selected_physical_cube_is_wild(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=2,
            wild_as="'",
        )
        state = GameState(
            self.universe,
            0,
            Division.CUSTOM,
            Situation.IMPOSSIBLE,
            resources=CubeInventory.parse("GG"),
            variations=config,
        )
        combined = match_cube_use(("G", "'"), state, CubeInventory())
        self.assertIsNotNone(combined)
        self.assertEqual(combined.physical.count("G"), 2)
        self.assertEqual(combined.wild_cube_id, "resources:G:2")
        self.assertIsNone(match_cube_use(("'", "'"), state, CubeInventory()))

    def test_required_wild_cube_must_be_used_and_can_move_with_state(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="required",
            wild_cube_ordinal=2,
            wild_as="'",
        )
        state = GameState(
            self.universe,
            0,
            Division.CUSTOM,
            Situation.FORCEOUT,
            required=CubeInventory.parse("GG"),
            variations=config,
        )
        self.assertIsNone(match_cube_use(("G",), state, state.required))
        use = match_cube_use(("G", "'"), state, state.required)
        self.assertIsNotNone(use)
        self.assertEqual(use.wild_cube_id, "required:G:2")

    def test_wild_cube_interpretation_must_match_across_complete_solution(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=1,
        )
        state = GameState(
            self.universe,
            0,
            Division.CUSTOM,
            Situation.IMPOSSIBLE,
            resources=CubeInventory.parse("G"),
            variations=config,
        )
        prime = match_cube_use(("'",), state, CubeInventory())
        union = match_cube_use(("u",), state, CubeInventory())
        self.assertIsNotNone(prime)
        self.assertIsNotNone(union)
        self.assertFalse(combined_resource_use_is_legal(prime, union, state))

    def test_illegal_declaration_is_reported_for_proceed_anyway_ui(self):
        config = VariationConfig(active=frozenset({Variation.SYMMETRIC_DIFFERENCE}))
        issues = validate_variations(Division.MIDDLE, self.universe, config)
        self.assertTrue(any("not normally available" in issue.message.lower() for issue in issues))

    def test_required_and_forbidden_cards_apply_to_physical_result(self):
        config = VariationConfig(
            active=frozenset({Variation.REQUIRED_FORBIDDEN_CARD}),
            required_card="B",
            forbidden_card="BR",
        )
        answers = check_expression(self.universe, "B U Z", variations=config)
        self.assertTrue(answers[0].violations)


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.universe = Universe.full()

    def state(self, required, permitted="", resources="", goal=6, situation=Situation.FORCEOUT, variations=VariationConfig()):
        return GameState(
            self.universe,
            goal,
            Division.CUSTOM,
            situation,
            required=CubeInventory.parse(required),
            permitted=CubeInventory.parse(permitted),
            resources=CubeInventory.parse(resources),
            variations=variations,
        )

    def test_solver_never_returns_a_differently_valued_interpretation(self):
        report = solve(self.state("BGRu-"), requested=6)
        self.assertGreater(report.returned, 0)
        for group in report.groups:
            for answer in group.answers:
                interpretations = enumerate_evaluations(answer.solution, self.universe)
                self.assertEqual({item.value for item in interpretations}, {6})

    def test_restriction_may_reduce_a_set_name_from_sixteen_to_goal(self):
        # This is the regression the legacy solver missed by prefiltering V U Z
        # to the Goal before applying B subset R.
        state = self.state("c", "BRVZu", goal=12)
        report = solve(state, requested=20)
        matches = [
            answer
            for group in report.groups
            for answer in group.answers
            if answer.solution in {"(V U Z)", "(Z U V)"}
        ]
        self.assertTrue(matches)
        self.assertTrue(all(answer.restriction for answer in matches))

    def test_prime_only_set_name_is_supported_but_one_cube_answer_is_not(self):
        prime = solve(self.state("B'", goal=8), requested=2)
        self.assertEqual(prime.returned, 1)
        one_cube = solve(self.state("B", goal=8), requested=2)
        self.assertEqual(one_cube.returned, 0)

    def test_situation_limits_actual_resource_inventory(self):
        now = solve(self.state("B", resources="'", goal=8, situation=Situation.NOW), requested=2)
        self.assertGreater(now.returned, 0)
        self.assertTrue(all(
            answer.cube_use.resource_cubes <= 1
            for group in now.groups for answer in group.answers
        ))

        forceout = solve(self.state("B", resources="'", goal=8, situation=Situation.FORCEOUT), requested=2)
        self.assertEqual(forceout.returned, 0)
        self.assertTrue(any("ignored" in warning for warning in forceout.warnings))

    def test_now_combines_resource_use_across_restriction_and_set_name(self):
        state = self.state("c", resources="BR", goal=1, situation=Situation.NOW)
        b_use = CubeUse(
            CubeInventory.parse("B"),
            CubeInventory.parse("B"),
            1,
            CubeInventory.parse("B"),
        )
        same_b = CubeUse(
            CubeInventory.parse("B"),
            CubeInventory.parse("B"),
            1,
            CubeInventory.parse("B"),
        )
        r_use = CubeUse(
            CubeInventory.parse("R"),
            CubeInventory.parse("R"),
            1,
            CubeInventory.parse("R"),
        )
        self.assertTrue(combined_resource_use_is_legal(b_use, same_b, state))
        self.assertFalse(combined_resource_use_is_legal(b_use, r_use, state))

    def test_now_does_not_conflate_wild_and_ordinary_same_face_resources(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=2,
            wild_as="'",
        )
        state = self.state(
            "",
            resources="GG",
            goal=1,
            situation=Situation.NOW,
            variations=config,
        )
        ordinary = match_cube_use(("G",), state, CubeInventory())
        wild = match_cube_use(("'",), state, CubeInventory())
        self.assertIsNotNone(ordinary)
        self.assertIsNotNone(wild)
        self.assertFalse(combined_resource_use_is_legal(ordinary, wild, state))

    def test_impossible_uses_actual_resources_and_state_validation_knows_cube_limits(self):
        impossible = solve(
            self.state("B", resources="'", goal=8, situation=Situation.IMPOSSIBLE),
            requested=2,
        )
        self.assertGreater(impossible.returned, 0)

        invalid = self.state("BBBBBBBBB", goal=1)
        errors, _ = validate_game_state(invalid)
        self.assertTrue(any("8" in error and "color cubes" in error for error in errors))

    def test_distinct_physical_card_sets_are_promoted_first(self):
        report = solve(self.state("BGRu-"), requested=3)
        self.assertEqual(report.returned, 3)
        self.assertEqual(len(report.groups), 3)

    def test_output_order_is_deterministic(self):
        state = self.state("BGRu-", goal=6)
        first = solve(state, requested=5)
        second = solve(state, requested=5)
        first_answers = [answer.solution for group in first.groups for answer in group.answers]
        second_answers = [answer.solution for group in second.groups for answer in group.answers]
        self.assertEqual(first_answers, second_answers)

    def test_solver_can_choose_blank_card_wild_assignment(self):
        config = VariationConfig(
            active=frozenset({Variation.BLANK_CARD_WILD}),
            blank_card_auto=True,
        )
        report = solve(
            self.state("Bu", "Z", goal=9, variations=config),
            requested=2,
            time_limit_seconds=5,
        )
        self.assertGreater(report.returned, 0)
        self.assertTrue(any(
            "Blank card is treated as" in note
            for group in report.groups
            for answer in group.answers
            for note in answer.variation_notes
        ))

    def test_solver_catalog_includes_symbols_supplied_only_by_wild_cube(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=1,
            wild_as="'",
        )
        report = solve(
            self.state(
                "B",
                resources="G",
                goal=8,
                situation=Situation.NOW,
                variations=config,
            ),
            requested=1,
        )
        answers = [answer for group in report.groups for answer in group.answers]
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0].solution, "B'")
        self.assertEqual(answers[0].cube_use.wild_cube_id, "resources:G:1")

    def test_solver_can_use_wild_cube_as_a_restriction_operator(self):
        config = VariationConfig(
            active=frozenset({Variation.WILD_CUBE}),
            wild_cube="G",
            wild_cube_section="resources",
            wild_cube_ordinal=1,
            wild_as="c",
        )
        report = solve(
            self.state(
                "B",
                permitted="R",
                resources="G",
                goal=4,
                situation=Situation.NOW,
                variations=config,
            ),
            requested=1,
        )
        answers = [answer for group in report.groups for answer in group.answers]
        self.assertEqual(len(answers), 1)
        self.assertIsNotNone(answers[0].restriction)
        self.assertIn("⊂", answers[0].restriction)
        self.assertTrue(answers[0].restriction_cube_use.wild_cube_used)

    def test_independent_restrictions_are_not_searched_when_regular_search_succeeds(self):
        state = self.state("c", "BRVZu", goal=12)
        with patch(
            "onsets_engine.solver._independent_restriction_candidates",
            side_effect=AssertionError("fallback should not run"),
        ):
            report = solve(state, requested=1)
        self.assertGreater(report.returned, 0)

    def test_independent_restriction_fallback_can_combine_separate_statements(self):
        state = self.state("cc", "BRGY", goal=1)
        first = enumerate_restriction_sets("B c R")[0][0]
        second = enumerate_restriction_sets("G c Y")[0][0]
        candidates = _independent_restriction_candidates(
            state,
            (first, second),
            monotonic() + 1,
            6,
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].display, "B ⊂ R; G ⊂ Y")
        self.assertEqual(candidates[0].cube_use.physical.count("c"), 2)

    def test_solver_uses_independent_restrictions_when_regular_ones_find_nothing(self):
        report = solve(
            self.state("cc", "BRGY", goal=3),
            requested=1,
            max_solution_cubes=3,
            max_restriction_cubes=6,
        )
        answers = [answer for group in report.groups for answer in group.answers]
        self.assertEqual(len(answers), 1)
        self.assertIn(";", answers[0].restriction)

    def test_impossible_no_result_message_is_plain(self):
        report = solve(
            self.state("B", goal=99, situation=Situation.IMPOSSIBLE),
            requested=1,
        )
        self.assertEqual(report.returned, 0)
        self.assertIn("Nothing was found.", report.warnings)


if __name__ == "__main__":
    unittest.main()
