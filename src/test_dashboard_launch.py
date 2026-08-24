#!/usr/bin/env python3
"""Tests for `dashboard_launch.py`'s singleton-spawn mechanism: the lock
that keeps concurrent MCP sessions from racing to start N dashboard
processes, and the health probe that tells a real dashboard apart from an
unrelated service or a crashed one. No import-time dependency on mcp or
fastapi, so this suite runs under the stdlib-only test command.

Run with `cd src && python3 -m unittest test_dashboard_launch -v`.
"""
import http.server
import os
import socket
import tempfile
import threading
import unittest

import dashboard_launch


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _serve(handler_class):
    server = http.server.HTTPServer(("127.0.0.1", 0), handler_class)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _stop(server):
    # shutdown() alone only stops serve_forever's loop -- it doesn't
    # release the listening socket, which left every caller leaking one
    # open fd per test.
    server.shutdown()
    server.server_close()


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # keep test output quiet


class _NotUsHandler(http.server.BaseHTTPRequestHandler):
    """A server that answers on the port but isn't our dashboard -- every
    path 404s, including the health endpoint."""

    def do_GET(self):
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):
        pass


class LockTests(unittest.TestCase):
    """flock is keyed to the open file description, not the process --
    two independent os.open() calls on the same path, even from this one
    test process, behave exactly as two competing sessions' locks would."""

    def test_second_opener_does_not_win_a_held_lock(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.lock")
            fd1 = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
            fd2 = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
            try:
                self.assertTrue(dashboard_launch._acquire_lock(fd1))
                self.assertFalse(dashboard_launch._acquire_lock(fd2))
            finally:
                dashboard_launch._release_lock(fd1)
                os.close(fd1)
                os.close(fd2)

    def test_lock_is_available_again_after_release(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.lock")
            fd1 = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
            fd2 = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
            try:
                self.assertTrue(dashboard_launch._acquire_lock(fd1))
                dashboard_launch._release_lock(fd1)
                self.assertTrue(dashboard_launch._acquire_lock(fd2))
            finally:
                dashboard_launch._release_lock(fd2)
                os.close(fd1)
                os.close(fd2)


class IsAliveTests(unittest.TestCase):
    def test_true_when_health_endpoint_answers(self):
        server = _serve(_HealthHandler)
        try:
            self.assertTrue(dashboard_launch.is_alive(server.server_port))
        finally:
            _stop(server)

    def test_false_when_nothing_is_listening(self):
        self.assertFalse(dashboard_launch.is_alive(_free_port()))

    def test_false_for_an_unrelated_service_on_the_port(self):
        # Proves this checks the app-level health path, not just "did
        # something answer on the TCP port" -- a stray service holding
        # the port must not read as our dashboard.
        server = _serve(_NotUsHandler)
        try:
            self.assertFalse(dashboard_launch.is_alive(server.server_port))
        finally:
            _stop(server)


class VenvPythonPathTests(unittest.TestCase):
    def _with_os_name(self, name):
        original = dashboard_launch.os.name
        dashboard_launch.os.name = name
        self.addCleanup(setattr, dashboard_launch.os, "name", original)

    def test_windows_path_shape(self):
        self._with_os_name("nt")
        path = dashboard_launch.venv_python_path("/repo")
        self.assertEqual(path, os.path.join("/repo", ".venv", "Scripts", "python.exe"))

    def test_posix_path_shape(self):
        self._with_os_name("posix")
        path = dashboard_launch.venv_python_path("/repo")
        self.assertEqual(path, os.path.join("/repo", ".venv", "bin", "python3"))


class UvicornArgvTests(unittest.TestCase):
    def test_shape(self):
        argv = dashboard_launch.uvicorn_argv("/venv/python3", "/repo/src", 8501)
        self.assertEqual(argv, [
            "/venv/python3", "-m", "uvicorn", "webui.app:app",
            "--app-dir", "/repo/src", "--port", "8501", "--host", "127.0.0.1",
        ])

    def test_port_is_stringified(self):
        argv = dashboard_launch.uvicorn_argv("/venv/python3", "/repo/src", 9000)
        self.assertIn("9000", argv)
        self.assertNotIn(9000, argv)


class DashboardUrlTests(unittest.TestCase):
    def test_dashboard_url_default_port(self):
        self.assertEqual(dashboard_launch.dashboard_url(), "http://localhost:8501")

    def test_dashboard_url_custom_port(self):
        self.assertEqual(dashboard_launch.dashboard_url(9000), "http://localhost:9000")


class EnsureRunningTests(unittest.TestCase):
    """The mechanism that matters: exactly one caller ever reaches
    `_spawn_detached`, however many "sessions" (patched `is_alive`/
    `find_spec` plus a real flock) contend for it at once."""

    def _patch(self, obj, name, value):
        original = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, original)

    def _force_fastapi_present(self):
        self._patch(dashboard_launch.importlib.util, "find_spec", lambda name: object())

    def test_does_nothing_when_already_alive(self):
        self._force_fastapi_present()
        calls = []
        self._patch(dashboard_launch, "is_alive", lambda *a, **k: True)
        self._patch(dashboard_launch, "_spawn_detached", lambda *a, **k: calls.append(a))
        with tempfile.TemporaryDirectory() as d:
            dashboard_launch.ensure_running(project_root=d)
        self.assertEqual(calls, [])

    def test_skips_spawn_when_fastapi_is_not_installed(self):
        self._patch(dashboard_launch.importlib.util, "find_spec", lambda name: None)
        calls = []
        self._patch(dashboard_launch, "is_alive", lambda *a, **k: False)
        self._patch(dashboard_launch, "_spawn_detached", lambda *a, **k: calls.append(a))
        with tempfile.TemporaryDirectory() as d:
            dashboard_launch.ensure_running(project_root=d)
        self.assertEqual(calls, [])

    def test_does_not_spawn_when_the_lock_is_already_held(self):
        self._force_fastapi_present()
        calls = []
        self._patch(dashboard_launch, "is_alive", lambda *a, **k: False)
        self._patch(dashboard_launch, "_spawn_detached", lambda *a, **k: calls.append(a))
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, ".claude"), exist_ok=True)
            lock_path = dashboard_launch._lock_path(d)
            holder_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
            self.assertTrue(dashboard_launch._acquire_lock(holder_fd))
            try:
                dashboard_launch.ensure_running(project_root=d)
            finally:
                dashboard_launch._release_lock(holder_fd)
                os.close(holder_fd)
        self.assertEqual(calls, [])

    def test_spawns_once_and_waits_for_liveness_when_the_lock_is_free(self):
        self._force_fastapi_present()
        calls = []
        # False on the pre-lock probe and the post-lock re-check, True from
        # _wait_until_alive's first poll on -- proves a fresh spawn is
        # actually followed by a liveness wait, not an instant return.
        responses = iter([False, False, True])
        self._patch(dashboard_launch, "is_alive", lambda *a, **k: next(responses, True))
        self._patch(dashboard_launch, "_spawn_detached", lambda *a, **k: calls.append(a))
        with tempfile.TemporaryDirectory() as d:
            dashboard_launch.ensure_running(project_root=d)
        self.assertEqual(len(calls), 1)

    def test_never_raises_out_of_an_unexpected_failure(self):
        # This runs inside a daemon thread nobody is watching -- an
        # unexpected exception must be logged, never propagated.
        self._force_fastapi_present()
        self._patch(dashboard_launch, "is_alive", lambda *a, **k: False)

        def _boom(*a, **k):
            raise RuntimeError("simulated spawn failure")

        self._patch(dashboard_launch, "_spawn_detached", _boom)
        with tempfile.TemporaryDirectory() as d:
            dashboard_launch.ensure_running(project_root=d)  # must not raise
            with open(dashboard_launch._log_path(d)) as f:
                self.assertIn("simulated spawn failure", f.read())


if __name__ == "__main__":
    unittest.main()
