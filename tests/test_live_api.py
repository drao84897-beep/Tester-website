import unittest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database import init_db, clear_history


class TestLiveApiAndWorkflows(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        init_db()

    def test_landing_page_renders(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"WEBVERIFY AI", resp.data)
        self.assertIn(b"Know What", resp.data)

    def test_ssrf_protection_blocked(self):
        # 127.0.0.1
        resp = self.client.post("/api/analyze", json={"url": "http://127.0.0.1:8080"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertIn("restricted for security", data["error"])

        # Cloud metadata
        resp_meta = self.client.post("/api/analyze", json={"url": "http://169.254.169.254/latest"})
        self.assertEqual(resp_meta.status_code, 400)

        # Localhost
        resp_lh = self.client.post("/api/analyze", json={"url": "http://localhost:5000"})
        self.assertEqual(resp_lh.status_code, 400)

    def test_invalid_url_format(self):
        resp = self.client.post("/api/analyze", json={"url": ""})
        self.assertEqual(resp.status_code, 400)

    def test_analyze_real_website(self):
        # Scan example.com
        resp = self.client.post("/api/analyze", json={"url": "https://example.com"})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        self.assertIn("score", data)
        self.assertIn("classification", data)
        self.assertIn("breakdown", data)
        self.assertIn("security", data)
        self.assertIn("domain", data)
        self.assertIn("ai_analysis", data)
        self.assertTrue(0 <= data["score"] <= 100)
        self.assertIn(data["classification"], ["LIKELY REAL BUSINESS", "NEEDS VERIFICATION", "LIKELY DEMO / DUMMY"])

        scan_id = data.get("id")
        self.assertIsNotNone(scan_id)

        # Test History retrieval
        hist_resp = self.client.get("/api/history")
        self.assertEqual(hist_resp.status_code, 200)
        history = json.loads(hist_resp.data)
        self.assertTrue(any(item["id"] == scan_id for item in history))

        # Test Report API
        rep_resp = self.client.get(f"/api/report/{scan_id}")
        self.assertEqual(rep_resp.status_code, 200)
        rep_data = json.loads(rep_resp.data)
        self.assertEqual(rep_data["id"], scan_id)

        # Test Printable Report HTML view
        rep_html = self.client.get(f"/report/{scan_id}")
        self.assertEqual(rep_html.status_code, 200)
        self.assertIn(b"Authenticity Report", rep_html.data)
        self.assertIn(b"Official Platform Disclaimer", rep_html.data)

        # Test Delete scan
        del_resp = self.client.delete(f"/api/history/{scan_id}")
        self.assertEqual(del_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
