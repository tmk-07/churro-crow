import json
import unittest

from onsets_engine.browser_api import dispatch_json


FULL_UNIVERSE = [
    "BR", "BRY", "BY", "B", "BRG", "BRGY", "BGY", "BG",
    "RG", "RGY", "GY", "G", "R", "RY", "Y", "blank",
]


def call(method, payload=None):
    return json.loads(dispatch_json(method, json.dumps(payload or {})))


class BrowserApiTests(unittest.TestCase):
    def test_config_uses_versioned_engine_contract(self):
        response = call("config")
        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["ruleset_id"], "agloa-2026-27")
        self.assertEqual(len(response["data"]["card_order"]), 16)

    def test_checker_returns_value_sorted_interpretations(self):
        response = call("check", {
            "universe": FULL_UNIVERSE,
            "solution": "B U G - R",
        })
        self.assertTrue(response["ok"])
        answers = response["data"]["answers"]
        self.assertEqual([answer["value"] for answer in answers], [6, 10])
        self.assertEqual(
            {answer["expression"] for answer in answers},
            {"((B U G) − R)", "(B U (G − R))"},
        )

    def test_solver_returns_unique_card_sets(self):
        response = call("solve", {
            "universe": FULL_UNIVERSE,
            "goal": 6,
            "situation": "forceout",
            "required": "BGRu-",
            "requested": 3,
        })
        self.assertTrue(response["ok"])
        groups = response["data"]["groups"]
        self.assertEqual(len(groups), 3)
        self.assertEqual(len({tuple(group["cards"]) for group in groups}), 3)

    def test_user_errors_cross_the_json_boundary(self):
        response = call("check", {"universe": FULL_UNIVERSE})
        self.assertFalse(response["ok"])
        self.assertEqual(response["message"], "Enter a Restriction, a Set-Name, or both.")


if __name__ == "__main__":
    unittest.main()
