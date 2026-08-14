import unittest

try:
    from streamlit.testing.v1 import AppTest
except ModuleNotFoundError:  # Keeps core tests runnable without UI dependencies.
    AppTest = None


@unittest.skipIf(AppTest is None, "Streamlit is not installed in this environment")
class StreamlitSmokeTests(unittest.TestCase):
    def _app(self):
        app = AppTest.from_file("main_streamlit.py")
        app.run(timeout=15)
        self.assertEqual(list(app.exception), [])
        return app

    def _page(self, path):
        app = self._app()
        app.switch_page(path).run(timeout=15)
        self.assertEqual(list(app.exception), [])
        return app

    def test_learn_page_loads(self):
        app = self._app()
        self.assertEqual(app.title[0].value, "Churro Crow")

    def test_all_navigation_pages_load(self):
        expected = {
            "pages/check.py": "Check an expression",
            "pages/solve.py": "Find Solutions",
            "pages/practice.py": "Practice",
            "pages/leaderboards.py": "Leaderboards",
        }
        for page, title in expected.items():
            with self.subTest(page=page):
                app = self._page(page)
                self.assertEqual(app.title[0].value, title)

    def test_checker_lists_every_legal_interpretation(self):
        app = self._page("pages/check.py")
        next(item for item in app.text_input if item.label == "Set-Name, optional").set_value(
            "B U G - R"
        )
        next(item for item in app.button if item.label == "Check expression").click()
        app.run(timeout=15)

        self.assertEqual(list(app.exception), [])
        expressions = {item.value for item in app.code}
        values = {item.value for item in app.metric if item.label == "Value"}
        self.assertIn("((B U G) − R)", expressions)
        self.assertIn("(B U (G − R))", expressions)
        self.assertEqual(values, {"6", "10"})
        self.assertEqual([tab.label for tab in app.tabs], ["Value 6 · 1", "Value 10 · 1"])

    def test_checker_hides_game_state_only_controls(self):
        app = self._page("pages/check.py")
        labels = {
            item.label
            for collection in (app.text_input, app.checkbox)
            for item in collection
        }
        self.assertNotIn("Shake cubes (only needed to declare Wild Cube or No Null)", labels)
        self.assertNotIn("Goal, optional", labels)
        self.assertNotIn("Wild Cube", labels)
        self.assertNotIn("Multiple Operations", labels)
        self.assertNotIn("U and ∩ Interchangeable", labels)
        self.assertNotIn("V and Z Interchangeable", labels)

    def test_checker_renders_all_interpretations_for_reported_restriction_case(self):
        app = self._page("pages/check.py")
        next(item for item in app.text_area if item.label == "Restriction(s), optional").set_value(
            "BcGuY=R-G"
        )
        next(item for item in app.text_input if item.label == "Set-Name, optional").set_value(
            "BuG-RuY'"
        )
        next(item for item in app.button if item.label == "Check expression").click()
        app.run(timeout=15)

        self.assertEqual(list(app.exception), [])
        values = [item.value for item in app.metric if item.label == "Value"]
        self.assertEqual(values, ["0", "1", "1", "2", "2"])
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Value 0 · 1", "Value 1 · 2", "Value 2 · 2"],
        )
        headings = [item.value for item in app.subheader]
        self.assertIn("Interpretation 5", headings)

    def test_solver_generates_grouped_results(self):
        app = self._page("pages/solve.py")
        card_buttons = {item.label for item in app.button}
        self.assertTrue({"✓ BR", "✓ BRGY", "✓ blank"} <= card_buttons)
        next(item for item in app.text_input if item.label == "Required").set_value("BGRu-")
        next(item for item in app.button if item.label == "Generate Solutions").click()
        app.run(timeout=15)

        self.assertEqual(list(app.exception), [])
        metrics = {item.label: item.value for item in app.metric}
        self.assertGreater(int(metrics["Unique solutions"]), 0)
        self.assertGreater(int(metrics["Written variations"]), 0)
        for expression in (item.value for item in app.code):
            if "⊂" not in expression and "=" not in expression:
                self.assertTrue(expression.startswith("(") or expression.endswith("'"))


if __name__ == "__main__":
    unittest.main()
