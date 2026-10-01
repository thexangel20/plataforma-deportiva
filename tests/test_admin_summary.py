import unittest
from unittest.mock import patch
import os

from app import app
from app.admin_summary import build_admin_summary
from app.repositories import LocalRepository


class AdminSummaryTestCase(unittest.TestCase):
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
        self.repository = LocalRepository()
        self.repository.set_active("futbol", True)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_summary_counts_total_active_and_inactive(self):
        self.repository.set_active("futbol", False)
        summary = build_admin_summary(self.repository.list_all(include_inactive=True))

        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["activos"], 3)
        self.assertEqual(summary["inactivos"], 1)

    def test_summary_distributes_cost_levels(self):
        summary = build_admin_summary(self.repository.list_all(include_inactive=True))

        self.assertEqual(summary["por_costo"], {"bajo": 2, "medio": 1, "alto": 1})

    def test_admin_summary_route_renders_statistics(self):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Resumen administrativo", response.data)
        self.assertIn(b"Total de deportes", response.data)
        self.assertIn("Distribución por nivel de costo".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
