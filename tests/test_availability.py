import os
import unittest
from unittest.mock import patch

from app import app
from app.repositories import LocalRepository


class AvailabilityTestCase(unittest.TestCase):
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

    def test_active_field_is_present_in_admin_data(self):
        sports = self.repository.list_all(include_inactive=True)

        self.assertIn("activo", sports[0])
        self.assertTrue(sports[0]["activo"])

    def test_deactivating_preserves_data_and_hides_public_sport(self):
        original = self.repository.get_by_ids(["futbol"])[0]
        updated = self.repository.set_active("futbol", False)

        self.assertEqual(updated["nombre"], original["nombre"])
        self.assertFalse(updated["activo"])
        self.assertEqual(self.repository.get_by_ids(["futbol"]), [])
        self.assertEqual(self.repository.list_all(include_inactive=True)[0]["id"], "futbol")

    def test_admin_route_changes_status_without_deleting_record(self):
        response = self.client.post(
            "/admin/deportes/futbol/estado",
            data={"activo": "false"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"desactivado correctamente", response.data)
        self.assertIn(b"Inactivo", response.data)

    def test_invalid_status_is_rejected(self):
        response = self.client.post(
            "/admin/deportes/futbol/estado",
            data={"activo": "invalid"},
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
