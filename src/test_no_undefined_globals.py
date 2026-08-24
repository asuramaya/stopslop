#!/usr/bin/env python3
"""Static check over every source file: does any function read a global
name the module never binds. Split out from the old test_dashboard.py at
the webui cutover -- everything else in that file was a regression guard
for bug classes specific to Streamlit's rerun/session-state model
(stale widgets, undo needing a manual key-clearing dance, callbacks that
must never call st.rerun()), none of which exist in the new webui/ --
every request there is stateless, rendered fresh from disk, with no
widget to go stale. This generic scanner is the one part of that file
with nothing Streamlit-specific about it, and it already covers webui/
automatically (it walks every .py file under src/).

The bug this scanner exists for: `dashboard.py` used to call
`st.set_page_config()` at module level, so importing it outside a
Streamlit run was not safe, and no test imported it. `ACTION_ICON`, a
module-level dict, was deleted during a refactor while its only use
stayed where it was. The Watch page raised `NameError:
name 'ACTION_ICON' is not defined` on every render, and the whole test
suite stayed green through two commits, because nothing ever executed
that line. An AST audit at the time did check for this class of mistake
and missed it, because it only looked at underscore-prefixed FUNCTION
names -- the shape of the previous bug, not the shape of the class. So
this uses `symtable`, which applies Python's real scoping rules instead
of a hand-written approximation of them, and covers every module-level
name: constants, functions, imports, classes.

Static, not an import: these tests read source and never execute it, so
adding a module here can never run its import-time side effects. Every
route module in webui/ IS safely importable now (no module-level
side-effecting calls the way dashboard.py's set_page_config() was), but
this scanner is cheap and general enough to keep running regardless.
"""
import builtins
import os
import symtable
import unittest

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SRC_DIR)

# Names the interpreter injects into every module. symtable reports them as
# global reads, and no source file assigns them. __path__ is injected only
# into a PACKAGE's __init__.py (its own subpackage search path) -- absent
# from a plain module, which is why nothing needed it here before
# rulesets/__init__.py started scanning its own subpackages with it.
MODULE_DUNDERS = {"__file__", "__name__", "__doc__", "__package__",
                   "__spec__", "__loader__", "__builtins__", "__path__"}


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

    def test_no_source_file_reads_a_name_it_does_not_define(self):
        for path in _python_files():
            with open(path) as f:
                source = f.read()
            with self.subTest(file=os.path.relpath(path, REPO_ROOT)):
                self.assertEqual(undefined_globals(source, path), [])


if __name__ == "__main__":
    unittest.main()
