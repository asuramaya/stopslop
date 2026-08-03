#!/usr/bin/env python3
"""Static checks over source files the test suite never imports.

`dashboard.py` calls `st.set_page_config()` at module level, so importing it
outside a Streamlit run is not safe, and no test imports it. That is a real
hole rather than a quirk: every OTHER module in this project gets its names
resolved the moment some test imports it, and a typo or a lost definition
surfaces immediately. The dashboard's names are resolved only when a human
opens the page.

That hole cost a live crash. `ACTION_ICON`, a module-level dict, was deleted
during the vocabulary refactor while its only use stayed where it was. The
Watch page raised `NameError: name 'ACTION_ICON' is not defined` on every
render, and the whole test suite stayed green through two commits, because
nothing ever executed that line.

An AST audit run at the time did check for this class of mistake and missed
it, because it only looked at underscore-prefixed FUNCTION names -- the
shape of the previous bug, not the shape of the class. So this uses
`symtable`, which applies Python's real scoping rules instead of a
hand-written approximation of them, and covers every module-level name:
constants, functions, imports, classes.

Static, not an import: these tests read source and never execute it, so
adding a module here can never run its import-time side effects.
"""
import builtins
import os
import symtable
import unittest

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SRC_DIR)

# Names the interpreter injects into every module. symtable reports them as
# global reads, and no source file assigns them.
MODULE_DUNDERS = {"__file__", "__name__", "__doc__", "__package__",
                   "__spec__", "__loader__", "__builtins__"}


def undefined_globals(source, path):
    """[(scope, name), ...] for every name a function reads as a global that
    the module never binds. Empty for a healthy file."""
    top = symtable.symtable(source, path, "exec")
    bound = {sym.get_name() for sym in top.get_symbols()
             if sym.is_assigned() or sym.is_imported() or sym.is_namespace()}
    known = bound | set(dir(builtins)) | MODULE_DUNDERS

    found = set()

    def walk(table):
        for sym in table.get_symbols():
            if sym.is_global() and sym.get_name() not in known:
                found.add((table.get_name(), sym.get_name()))
        for child in table.get_children():
            walk(child)

    walk(top)
    return sorted(found)


def _python_files():
    out = []
    for root, dirs, names in os.walk(SRC_DIR):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".venv"}]
        out.extend(os.path.join(root, n) for n in names if n.endswith(".py"))
    out.append(os.path.join(REPO_ROOT, "stopslop.py"))
    return sorted(out)


class NoUndefinedGlobalsTests(unittest.TestCase):

    def test_the_scanner_finds_a_name_that_was_actually_deleted(self):
        """Guards the guard. A checker that reports nothing on healthy code
        and nothing on broken code is worse than no checker, because the
        green result reads as evidence."""
        source = "import os\n\nGREETING = 'hi'\n\ndef f():\n    return GREETING + os.sep\n"
        self.assertEqual(undefined_globals(source, "ok.py"), [])
        deleted = source.replace("GREETING = 'hi'", "UNUSED = 'hi'")
        self.assertEqual(undefined_globals(deleted, "broken.py"), [("f", "GREETING")])

    def test_dashboard_reads_no_name_it_does_not_define(self):
        path = os.path.join(SRC_DIR, "dashboard.py")
        with open(path) as f:
            source = f.read()
        self.assertEqual(
            undefined_globals(source, path), [],
            "dashboard.py reads a global it never binds. No test imports this "
            "module (set_page_config runs at import time), so this is the only "
            "thing standing between that and a live NameError on the page.")

    def test_no_source_file_reads_a_name_it_does_not_define(self):
        for path in _python_files():
            with open(path) as f:
                source = f.read()
            with self.subTest(file=os.path.relpath(path, REPO_ROOT)):
                self.assertEqual(undefined_globals(source, path), [])


class DashboardStructureTests(unittest.TestCase):
    """The two module-level facts a reader of the page depends on."""

    def setUp(self):
        with open(os.path.join(SRC_DIR, "dashboard.py")) as f:
            self.source = f.read()

    def test_every_gate_action_the_history_log_writes_has_an_icon(self):
        # ACTION_ICON.get() has a default, so a missing entry degrades
        # quietly rather than raising -- which is why the dict drifting out
        # of step with core.history needs asserting rather than trusting.
        scope = {}
        exec(compile(self.source[self.source.index("ACTION_ICON = {"):
                     self.source.index("def _status_footer")], "x", "exec"), scope)
        for action in ("deny", "auto_fix", "clean", "unscoped_write"):
            self.assertIn(action, scope["ACTION_ICON"])


if __name__ == "__main__":
    unittest.main()
