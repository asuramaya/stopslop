#!/usr/bin/env python3
"""Smoke tests for the webui skeleton -- every page route boots, the
static assets and the status footer fragment serve. In-process via
fastapi.testclient.TestClient, no real server or browser needed.

webui/app.py imports fastapi at module level, so this whole file is
skipped (not failed) when it's not installed -- the stdlib-only core
suite must stay runnable without the venv, same posture
test_mcp_server.py already takes for the `mcp` package (see its own
docstring).

Run with (needs the venv -- see README's MCP/dashboard setup section):
    cd src && ../.venv/bin/python3 -m unittest webui.test_app -v
"""
import unittest

try:
    from fastapi.testclient import TestClient

    from webui.app import app
    client = TestClient(app)
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class PageRouteTests(unittest.TestCase):
    def test_root_redirects_to_watch(self):
        response = client.get("/", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertTrue(response.headers["location"].endswith("/watch"))

    def test_every_page_route_boots(self):
        for path in ("/watch", "/checks", "/vocabulary", "/routing"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("stopslop", response.text)

    def test_active_nav_link_is_marked(self):
        response = client.get("/checks")
        self.assertIn('href="/checks" class="active"', response.text)

    def test_health(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class StatusFooterTests(unittest.TestCase):
    def test_status_fragment_boots_and_reports_real_numbers(self):
        response = client.get("/status/fragment")
        self.assertEqual(response.status_code, 200)
        self.assertIn("events", response.text)

    def test_status_footer_included_on_a_full_page(self):
        response = client.get("/watch")
        self.assertIn('id="status-footer"', response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class StaticAssetTests(unittest.TestCase):
    def test_htmx_is_vendored_and_served(self):
        response = client.get("/static/htmx.min.js")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 1000)

    def test_stylesheet_is_served(self):
        response = client.get("/static/style.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
