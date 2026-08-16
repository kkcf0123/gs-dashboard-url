import unittest
from datetime import datetime, timezone

from scripts.update_dashboard_url import dashboard_payload, normalize_dashboard_url


class DashboardUrlTests(unittest.TestCase):
    def test_normalizes_quick_tunnel_url(self):
        self.assertEqual(
            normalize_dashboard_url("https://Example-One.trycloudflare.com/"),
            "https://example-one.trycloudflare.com",
        )

    def test_rejects_non_quick_tunnel_host(self):
        with self.assertRaises(ValueError):
            normalize_dashboard_url("https://example.com")

    def test_rejects_credentials_path_query_and_port(self):
        invalid_urls = [
            "https://user@example.trycloudflare.com",
            "https://example.trycloudflare.com/dashboard",
            "https://example.trycloudflare.com?token=value",
            "https://example.trycloudflare.com:8443",
        ]
        for value in invalid_urls:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_dashboard_url(value)

    def test_payload_has_stable_shape(self):
        payload = dashboard_payload(
            "https://sample.trycloudflare.com",
            datetime(2026, 8, 16, 12, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(
            payload,
            {
                "schema_version": 1,
                "url": "https://sample.trycloudflare.com",
                "updated_at": "2026-08-16T12:30:00Z",
                "source": "gs-ops-bot",
            },
        )


if __name__ == "__main__":
    unittest.main()
