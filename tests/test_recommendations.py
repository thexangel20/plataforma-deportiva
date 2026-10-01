import unittest

from app import app
from app.recommendations import cost_level, recommend_deportes
from app.repositories import LocalRepository


class RecommendationTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.deportes = LocalRepository().list_all()

    def test_cost_level_is_derived_from_numeric_cost(self):
        self.assertEqual(cost_level(120), "bajo")
        self.assertEqual(cost_level(200), "medio")
        self.assertEqual(cost_level(300), "alto")

    def test_recommendations_match_all_selected_preferences(self):
        results = recommend_deportes(
            self.deportes,
            costo="bajo",
            objetivo="Agilidad y coordinación",
            tiempo=90,
        )

        self.assertEqual([sport["id"] for sport in results], ["baloncesto"])

    def test_recommendations_return_empty_when_no_sport_matches(self):
        results = recommend_deportes(self.deportes, tiempo=30)

        self.assertEqual(results, [])

    def test_recommendation_route_renders_form(self):
        response = self.client.get("/recomendar")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Obtener recomendaciones", response.data)
        self.assertIn(b"Nivel de costo", response.data)

    def test_recommendation_route_renders_matching_result(self):
        response = self.client.post(
            "/recomendar",
            data={"costo": "bajo", "objetivo": "Agilidad y coordinación", "tiempo": "90"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Baloncesto".encode(), response.data)
        self.assertNotIn("No encontramos coincidencias".encode(), response.data)

    def test_recommendation_route_shows_no_matches_message(self):
        response = self.client.post(
            "/recomendar",
            data={"costo": "alto", "objetivo": "Resistencia y trabajo en equipo", "tiempo": "30"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("No encontramos coincidencias".encode(), response.data)
