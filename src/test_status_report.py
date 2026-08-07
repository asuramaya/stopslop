#!/usr/bin/env python3
"""Tests for `status_report.py`'s installation-completeness checks: the
pre-commit hook marker, the venv/mcp/streamlit importability probe (and
its caching -- see `_venv_status`'s own docstring for why this one check is
cached when nothing else in this module is), and the MCP trust-state
reader.

Run with `cd src && python3 -m unittest test_status_report -v`.
"""
import json
import os
import sys
import tempfile
import unittest

import status_report


class ImportableTests(unittest.TestCase):
    def test_true_for_a_real_stdlib_module(self):
        self.assertTrue(status_report._importable(sys.executable, "os"))

    def test_false_for_a_nonexistent_module(self):
        self.assertFalse(status_report._importable(sys.executable, "definitely_not_a_real_module_xyz"))

    def test_false_when_the_interpreter_path_does_not_exist(self):
        self.assertFalse(status_report._importable("/nonexistent/python3", "os"))


class VenvStatusTests(unittest.TestCase):
    def setUp(self):
        status_report._venv_status.cache_clear()
        self.addCleanup(status_report._venv_status.cache_clear)

    def _patch_venv_python_path(self, value):
        original = status_report.dashboard_launch.venv_python_path
        status_report.dashboard_launch.venv_python_path = lambda root: value
        self.addCleanup(setattr, status_report.dashboard_launch, "venv_python_path", original)

    def test_reports_absent_without_spawning_a_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch_venv_python_path(os.path.join(tmp, "nope", "python3"))
            calls = []
            original_run = status_report.subprocess.run
            status_report.subprocess.run = lambda *a, **k: calls.append(a)
            try:
                result = status_report._venv_status(tmp)
            finally:
                status_report.subprocess.run = original_run
            self.assertEqual(result, (False, False, False))
            self.assertEqual(calls, [])

    def test_present_and_importable_reports_a_real_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch_venv_python_path(sys.executable)
            present, mcp_ok, streamlit_ok = status_report._venv_status(tmp)
            self.assertTrue(present)
            # mcp/streamlit availability depends on which interpreter runs
            # this suite (stdlib-only vs the real venv) -- just confirm a
            # real check ran, not a fixed answer either way.
            self.assertIsInstance(mcp_ok, bool)
            self.assertIsInstance(streamlit_ok, bool)

    def test_result_is_cached_across_calls_for_the_same_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._patch_venv_python_path(sys.executable)
            first = status_report._venv_status(tmp)
            calls = []
            original_run = status_report.subprocess.run
            status_report.subprocess.run = lambda *a, **k: calls.append(a)
            try:
                second = status_report._venv_status(tmp)
            finally:
                status_report.subprocess.run = original_run
            self.assertEqual(first, second)
            self.assertEqual(calls, [])  # cached -- no new subprocess spawned


class PrecommitHookInstalledTests(unittest.TestCase):
    def test_true_when_marker_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            hooks_dir = os.path.join(tmp, ".git", "hooks")
            os.makedirs(hooks_dir)
            with open(os.path.join(hooks_dir, "pre-commit"), "w") as f:
                f.write("#!/bin/sh\n# installed by stopslop.py init\nexec python3 x precommit\n")
            self.assertTrue(status_report._precommit_hook_installed(tmp))

    def test_false_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(status_report._precommit_hook_installed(tmp))

    def test_false_for_a_foreign_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            hooks_dir = os.path.join(tmp, ".git", "hooks")
            os.makedirs(hooks_dir)
            with open(os.path.join(hooks_dir, "pre-commit"), "w") as f:
                f.write("#!/bin/sh\necho not stopslop\n")
            self.assertFalse(status_report._precommit_hook_installed(tmp))


class McpTrustStatusTests(unittest.TestCase):
    def test_hook_not_wired_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = status_report._mcp_trust_status(tmp)
        self.assertIn("not wired up", result)

    def test_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_dir = os.path.join(tmp, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
                json.dump({"enabledMcpjsonServers": ["stopslop"]}, f)
            result = status_report._mcp_trust_status(tmp)
        self.assertEqual(result, "trusted")

    def test_not_yet_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_dir = os.path.join(tmp, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
                json.dump({"hooks": {}}, f)
            result = status_report._mcp_trust_status(tmp)
        self.assertIn("not yet approved", result)

    def test_unreadable_settings_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            claude_dir = os.path.join(tmp, ".claude")
            os.makedirs(claude_dir)
            with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
                f.write("{not valid json")
            result = status_report._mcp_trust_status(tmp)
        self.assertIn("unknown", result)


class BuildStatusReportIntegrationTests(unittest.TestCase):
    """Against the real repo -- read-only, same convention `test_mcp_server.py`
    already uses for its read-only tools (real registered rulesets, no
    fixture project)."""

    def test_new_fields_are_present_and_well_typed(self):
        report = status_report.build_status_report()
        self.assertIsInstance(report["precommit_hook_installed"], bool)
        self.assertIsInstance(report["venv_present"], bool)
        self.assertIsInstance(report["mcp_package_installed"], bool)
        self.assertIsInstance(report["streamlit_installed"], bool)
        self.assertIsInstance(report["mcp_trust"], str)
        self.assertIsInstance(report["dashboard_reachable"], bool)

    def test_format_status_report_renders_installation_section(self):
        report = status_report.build_status_report()
        text = status_report.format_status_report(report)
        self.assertIn("Installation", text)
        self.assertIn("Pre-commit gate:", text)
        self.assertIn("Virtualenv:", text)
        self.assertIn("MCP trust:", text)
        self.assertIn("Dashboard:", text)


if __name__ == "__main__":
    unittest.main()
