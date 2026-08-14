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

    def test_solver_generates_grouped_results(self):
        app = self._page("pages/solve.py")
        next(item for item in app.text_input if item.label == "Required").set_value("BGRu-")
        next(item for item in app.button if item.label == "Generate Solutions").click()
        app.run(timeout=15)

        self.assertEqual(list(app.exception), [])
        metrics = {item.label: item.value for item in app.metric}
        self.assertGreater(int(metrics["Solutions"]), 0)
        self.assertGreater(int(metrics["Different card sets"]), 0)
        for expression in (item.value for item in app.code):
            if "⊂" not in expression and "=" not in expression:
                self.assertTrue(expression.startswith("(") or expression.endswith("'"))


if __name__ == "__main__":
    unittest.main()
