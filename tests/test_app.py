"""Basic endpoint checks. Run with: python -m unittest discover -s tests"""
import unittest

import app as crimesight


class CrimeSightRoutesTest(unittest.TestCase):
    def setUp(self):
        crimesight.app.config["TESTING"] = True
        self.client = crimesight.app.test_client()

    def test_dashboard_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CrimeSight", response.data)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["dataset_loaded"])

    def test_summary_endpoint(self):
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json["records"], 0)

    def test_records_endpoint(self):
        response = self.client.get("/api/records?limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.json["count_returned"], 2)

    def test_invalid_records_query(self):
        response = self.client.get("/api/records?year=not-a-year")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
