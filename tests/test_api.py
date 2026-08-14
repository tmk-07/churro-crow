import unittest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    TestClient = None

if TestClient is not None:
    from api.app import app


@unittest.skipIf(TestClient is None, "FastAPI test dependencies are not installed")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_and_config_publish_the_versioned_contract(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["ruleset_id"], "agloa-2026-27")

        config = self.client.get("/api/config")
        self.assertEqual(config.status_code, 200)
        self.assertEqual(len(config.json()["card_order"]), 16)
        self.assertIn("senior", config.json()["available_variations"])

    def test_checker_returns_value_sorted_interpretations(self):
        response = self.client.post("/api/check", json={
            "universe": [
                "BR", "BRY", "BY", "B", "BRG", "BRGY", "BGY", "BG",
                "RG", "RGY", "GY", "G", "R", "RY", "Y", "blank",
            ],
            "solution": "B U G - R",
        })
        self.assertEqual(response.status_code, 200)
        answers = response.json()["answers"]
        self.assertEqual([answer["value"] for answer in answers], [6, 10])
        self.assertEqual(
            {answer["expression"] for answer in answers},
            {"((B U G) − R)", "(B U (G − R))"},
        )

    def test_restriction_only_check_returns_removed_cards(self):
        response = self.client.post("/api/check", json={
            "universe": ["BR", "B", "R", "Y"],
            "restriction": "B c R",
        })
        self.assertEqual(response.status_code, 200)
        interpretations = response.json()["restriction_interpretations"]
        self.assertEqual(len(interpretations), 1)
        self.assertEqual(
            interpretations[0]["restrictions"][0]["removed_cards"],
            ["B"],
        )

    def test_solver_counts_unique_card_sets_and_serializes_alternates(self):
        response = self.client.post("/api/solve", json={
            "universe": [
                "BR", "BRY", "BY", "B", "BRG", "BRGY", "BGY", "BG",
                "RG", "RGY", "GY", "G", "R", "RY", "Y", "blank",
            ],
            "goal": 6,
            "situation": "forceout",
            "required": "BGRu-",
            "requested": 3,
        })
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["returned"], 3)
        self.assertEqual(len(payload["groups"]), 3)
        self.assertEqual(
            len({tuple(group["cards"]) for group in payload["groups"]}),
            3,
        )

    def test_invalid_variation_can_be_reviewed_before_override(self):
        payload = {
            "universe": ["B", "R", "blank"],
            "solution": "B U R",
            "division": "elementary",
            "variations": {"active": ["double_set"]},
        }
        blocked = self.client.post("/api/check", json=payload)
        self.assertEqual(blocked.status_code, 422)
        self.assertTrue(blocked.json()["detail"]["issues"])

        payload["proceed_anyway"] = True
        proceeded = self.client.post("/api/check", json=payload)
        self.assertEqual(proceeded.status_code, 200)
        self.assertIn(
            "Enter the set that counts double.",
            proceeded.json()["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
