import unittest

from app import app


class ComparisonRoutesTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_catalog_has_comparison_controls(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Comparar seleccionados", response.data)
        self.assertIn(b"futbol", response.data)

    def test_comparison_requires_at_least_two_sports(self):
        response = self.client.get("/comparar?ids=futbol")

        self.assertEqual(response.status_code, 400)
        self.assertIn("al menos dos".encode(), response.data)

    def test_comparison_renders_selected_sports(self):
        response = self.client.get("/comparar?ids=futbol&ids=natacion")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Fútbol".encode(), response.data)
        self.assertIn("Natación".encode(), response.data)
        self.assertIn("Equipamiento".encode(), response.data)
        self.assertIn("Recomendaciones".encode(), response.data)

    def test_comparison_accepts_comma_separated_ids(self):
        response = self.client.get("/comparar?ids=futbol,natacion")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Comparar deportes".encode(), response.data)

    def test_comparison_rejects_unknown_sports(self):
        response = self.client.get("/comparar?ids=futbol&ids=no-existe")

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
