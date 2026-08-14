import unittest

import churrooscalc
from onsets_rules import (
    AUTOMATIC_VARIATIONS,
    RULESET_ID,
    Division,
    SolutionSituation,
    card_constraints_satisfied,
    enumerate_interpretations,
    no_null_restrictions_satisfied,
    normalize_notation,
    resource_cube_limit,
    resource_use_is_legal,
    two_solutions_satisfied,
    universe_size_warning,
)


class FullUniverseTestCase(unittest.TestCase):
    def setUp(self):
        self.original_universe = churrooscalc.universe
        self.original_operation_map = churrooscalc.op_map.copy()
        churrooscalc.universe = churrooscalc.cards.copy()
        churrooscalc.universeRefresher()
        churrooscalc.computed_sets.clear()

    def tearDown(self):
        churrooscalc.universe = self.original_universe
        churrooscalc.op_map.clear()
        churrooscalc.op_map.update(self.original_operation_map)
        churrooscalc.universeRefresher()
        churrooscalc.computed_sets.clear()


class RulesetMetadataTests(unittest.TestCase):
    def test_ruleset_is_versioned(self):
        self.assertEqual(RULESET_ID, "agloa-2026-27")

    def test_junior_and_senior_automatic_variations(self):
        expected = {
            "multiple_operations",
            "union_intersection_interchangeable",
            "universe_null_interchangeable",
        }
        self.assertEqual(AUTOMATIC_VARIATIONS[Division.JUNIOR], expected)
        self.assertEqual(AUTOMATIC_VARIATIONS[Division.SENIOR], expected)

    def test_division_universe_sizes_warn_but_do_not_block(self):
        self.assertIsNone(universe_size_warning(Division.MIDDLE, 12))
        self.assertIn("6-12", universe_size_warning(Division.MIDDLE, 5))
        self.assertIn("10-14", universe_size_warning(Division.SENIOR, 9))
        self.assertIsNone(universe_size_warning(Division.CUSTOM, 1))

    def test_game_situations_apply_official_resource_limits(self):
        self.assertEqual(resource_cube_limit(SolutionSituation.NOW), 1)
        self.assertEqual(resource_cube_limit(SolutionSituation.FORCEOUT), 0)
        self.assertIsNone(resource_cube_limit(SolutionSituation.IMPOSSIBLE))
        self.assertTrue(resource_use_is_legal(SolutionSituation.NOW, 1))
        self.assertFalse(resource_use_is_legal(SolutionSituation.NOW, 2))
        self.assertFalse(resource_use_is_legal(SolutionSituation.FORCEOUT, 1))
        self.assertTrue(resource_use_is_legal(SolutionSituation.IMPOSSIBLE, 8))


class VariationContractTests(unittest.TestCase):
    def test_no_null_does_not_require_a_restriction(self):
        self.assertTrue(no_null_restrictions_satisfied([]))

    def test_no_null_requires_removal_in_every_application_order(self):
        self.assertTrue(no_null_restrictions_satisfied([[1, 2], [3, 1]]))
        self.assertFalse(no_null_restrictions_satisfied([[1, 0], [2, 1]]))
        self.assertFalse(no_null_restrictions_satisfied([[]]))

    def test_two_solutions_uses_directed_physical_card_difference(self):
        self.assertTrue(two_solutions_satisfied(["B", "R"], ["B", "G"]))
        self.assertFalse(two_solutions_satisfied(["B", "R"], ["B", "R"]))
        self.assertFalse(two_solutions_satisfied(["B", "R"], ["B"]))

    def test_required_and_forbidden_cards_apply_to_final_set(self):
        cards = ["B", "BR", "blank"]
        self.assertTrue(card_constraints_satisfied(cards, required_card="blank"))
        self.assertFalse(card_constraints_satisfied(cards, required_card="G"))
        self.assertFalse(card_constraints_satisfied(cards, forbidden_card="BR"))


class NotationTests(unittest.TestCase):
    def test_keyboard_and_mathematical_aliases_normalize(self):
        self.assertEqual(normalize_notation("[b ∪ r] ∩ ∅"), "(BuR)nZ")
        self.assertEqual(normalize_notation("B /\\ R"), "BZR")
        self.assertEqual(normalize_notation("B ⊂ R"), "BcR")

    def test_unknown_symbols_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown On-Sets symbol"):
            normalize_notation("B + R")


class InterpretationTests(FullUniverseTestCase):
    def test_official_ambiguous_example_returns_every_grouping(self):
        results = enumerate_interpretations("B U G - R", churrooscalc.universe)

        self.assertEqual(
            {result.expression for result in results},
            {"((B U G) − R)", "(B U (G − R))"},
        )
        self.assertEqual({result.value for result in results}, {6, 10})

    def test_prime_has_priority_over_union(self):
        results = enumerate_interpretations("R U G'", churrooscalc.universe)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].expression, "(R U G')")
        self.assertEqual(results[0].value, 12)

    def test_explicit_grouping_removes_ambiguity(self):
        results = enumerate_interpretations("(B U G) - R", churrooscalc.universe)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].expression, "((B U G) − R)")
        self.assertEqual(results[0].value, 6)

    def test_prime_may_apply_to_a_group(self):
        results = enumerate_interpretations("(B U G)'", churrooscalc.universe)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].expression, "(B U G)'")
        self.assertEqual(results[0].value, 4)

    def test_symmetric_difference_changes_minus_interpretation(self):
        standard = enumerate_interpretations("B - R", churrooscalc.universe)
        symmetric = enumerate_interpretations(
            "B - R",
            churrooscalc.universe,
            symmetric_difference=True,
        )

        self.assertEqual(standard[0].value, 4)
        self.assertEqual(symmetric[0].value, 8)

    def test_malformed_expressions_have_useful_errors(self):
        invalid = {
            "B U": "end with a binary operation",
            "B R": "Expected a binary operation",
            "(B U R": "no matching closing",
            "'B": "Complement must follow",
        }
        for expression, message in invalid.items():
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(ValueError, message):
                    enumerate_interpretations(expression, churrooscalc.universe)


class LegacyCoreCompatibilityTests(FullUniverseTestCase):
    def test_official_basic_operation_examples(self):
        self.assertEqual(len(churrooscalc.set_cards("BuG", calcV=True)), 12)
        self.assertEqual(len(churrooscalc.set_cards("RnY", calcV=True)), 4)
        self.assertEqual(len(churrooscalc.set_cards("B-Y", calcV=True)), 4)
        self.assertEqual(len(churrooscalc.set_cards("G'", calcV=True)), 8)

    def test_subset_restriction_removes_only_counterexamples(self):
        restricted = churrooscalc.parseR("BcR'", calcV=True)
        expected = {
            card
            for card, dots in churrooscalc.universe.items()
            if not ("b" in dots and "r" in dots)
        }
        self.assertEqual(restricted, expected)

    def test_chain_restriction_applies_each_adjacent_relation(self):
        restricted = churrooscalc.parseR("BcRcG", calcV=True)
        expected = {
            card
            for card, dots in churrooscalc.universe.items()
            if not ("b" in dots and "r" not in dots)
            and not ("r" in dots and "g" not in dots)
        }
        self.assertEqual(restricted, expected)

    def test_required_cubes_are_reused_across_restriction_and_set_name(self):
        valid, message = churrooscalc.validate_inventory_inputs("BRuc", "G")
        self.assertTrue(valid, message)

    def test_optional_restriction_inventory_is_allowed(self):
        valid, message = churrooscalc.validate_inventory_inputs("BRu", "Gc")
        self.assertTrue(valid, message)

    def test_custom_universe_changes_v_z_and_complement(self):
        churrooscalc.universe = {
            "B": churrooscalc.cards["B"],
            "R": churrooscalc.cards["R"],
            "BR": churrooscalc.cards["BR"],
            "blank": churrooscalc.cards["blank"],
        }
        churrooscalc.universeRefresher()

        self.assertEqual(set(churrooscalc.set_cards("V", calcV=True)), set(churrooscalc.universe))
        self.assertEqual(churrooscalc.set_cards("Z", calcV=True), [])
        self.assertEqual(set(churrooscalc.set_cards("B'", calcV=True)), {"R", "blank"})

    def test_double_set_adds_weighted_card_entries(self):
        churrooscalc.double_set("B")

        self.assertEqual(len(churrooscalc.set_cards("B", calcV=True)), 16)
        self.assertEqual(len(churrooscalc.set_cards("V", calcV=True)), 24)


if __name__ == "__main__":
    unittest.main()
