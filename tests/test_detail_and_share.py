import os
import unittest
from unittest.mock import patch

from app import app


class DetailAndShareTestCase(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "",
                "SUPABASE_KEY": "",
                "SUPABASE_SERVICE_ROLE_KEY": "",
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_detail_route_has_stable_shareable_url(self):
        response = self.client.get("/deporte/futbol")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"F\xc3\xbAtbol", response.data)
        self.assertIn(b"Compartir deporte", response.data)
        self.assertIn(b"/deporte/futbol", response.data)

    def test_unknown_detail_returns_not_found(self):
        response = self.client.get("/deporte/no-existe")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"no existe", response.data)

    def test_catalog_links_to_each_detail(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/deporte/futbol", response.data)
        self.assertIn(b"/deporte/tenis", response.data)


if __name__ == "__main__":
    unittest.main()
