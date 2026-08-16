import base64
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.update_dashboard_url import dashboard_payload, normalize_dashboard_url, update_dashboard_file


def encoded_file(payload, sha="abc123"):
    content = json.dumps(payload).encode("utf-8")
    return {"sha": sha, "content": base64.b64encode(content).decode("ascii")}


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

    @patch("scripts.update_dashboard_url.github_request")
    def test_skips_commit_when_url_is_unchanged(self, request):
        request.return_value = encoded_file({
            "schema_version": 1,
            "url": "https://same.trycloudflare.com",
        })
        result = update_dashboard_file(
            "kkcf0123/gs-dashboard-url",
            "main",
            "test-token",
            "https://same.trycloudflare.com/",
        )
        self.assertFalse(result["changed"])
        request.assert_called_once()

    @patch("scripts.update_dashboard_url.github_request")
    def test_updates_file_when_url_changes(self, request):
        request.side_effect = [
            encoded_file({"schema_version": 1, "url": "https://old.trycloudflare.com"}),
            {"commit": {"sha": "new-commit"}},
        ]
        result = update_dashboard_file(
            "kkcf0123/gs-dashboard-url",
            "main",
            "test-token",
            "https://new.trycloudflare.com",
        )
        self.assertTrue(result["changed"])
        _, update_call = request.call_args_list
        self.assertEqual(update_call.kwargs["method"], "PUT")


if __name__ == "__main__":
    unittest.main()
