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
import ast
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
        for action in ("deny", "auto_fix", "clean", "unscoped_write",
                        "config_write"):
            self.assertIn(action, scope["ACTION_ICON"])


# Widgets whose value is only ever READ during a render -- a search box, a
# filter, the path being inspected, the pending entry in an add form. These
# never write to the config file, so a stale session value is harmless.
READ_ONLY_WIDGET_KEYS = ("rules_q", "add_", "note_", "attach_", "override_reason",
                          "watch_filter", "packlist::", "routing_focus",
                          "check_contents::")

MUTATING_WIDGETS = ("selectbox", "toggle", "number_input", "checkbox", "radio",
                     "segmented_control", "multiselect")


def _key_literal(call):
    """The static prefix of a call's `key=` argument, or None. Keys are
    often f-strings (`f"chk::{ruleset}::{check}"`); the leading constant is
    what identifies the widget's purpose."""
    for kw in call.keywords:
        if kw.arg != "key":
            continue
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
        if isinstance(kw.value, ast.JoinedStr):
            first = kw.value.values[0] if kw.value.values else None
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                return first.value
        return ""
    return None


class ApplyOnChangeTests(unittest.TestCase):
    """A keyed Streamlit widget returns SESSION STATE, not a fresh render of
    the data behind it, so the natural shape for instant-save --

        value = st.selectbox(..., key="k")
        if value != stored: write(value)

    -- fires whenever the STORED value changes for a reason the widget did
    not cause. It is a silent write with nobody having touched anything.

    This is not hypothetical. The Configure page's scope selector used one
    key for every routing rule, so the box carried `slopwatch` across a
    change of path and re-routed `*.md` away from ste100 IN THE CONFIG FILE,
    on page load. Two other controls (the enabled toggle, the threshold
    input) had the same shape and had not yet been caught.

    `on_change` fires only on genuine interaction. Any widget on the config
    page that can write must use it."""

    def _calls(self, path):
        with open(path) as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in MUTATING_WIDGETS:
                yield node

    def test_every_writable_widget_applies_on_change(self):
        path = os.path.join(SRC_DIR, "configure.py")
        for call in self._calls(path):
            key = _key_literal(call)
            if key is None:
                continue                       # unkeyed: no session state to go stale
            if key.startswith(READ_ONLY_WIDGET_KEYS):
                continue
            names = {kw.arg for kw in call.keywords}
            with self.subTest(widget=f"{call.func.attr}(key={key!r})", line=call.lineno):
                self.assertIn(
                    "on_change", names,
                    f"line {call.lineno}: this widget has a key, so its value "
                    f"outlives the data behind it. Either apply through "
                    f"on_change, or add its key prefix to READ_ONLY_WIDGET_KEYS "
                    f"to state that it never writes.")

    def test_no_callback_calls_st_rerun(self):
        """Streamlit reruns after a callback on its own, and calling rerun
        inside one raises. Callbacks are named by on_change= arguments."""
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        callbacks = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "on_change" and isinstance(kw.value, ast.Name):
                        callbacks.add(kw.value.id)
        self.assertTrue(callbacks, "no on_change callbacks found -- has the "
                                    "apply-on-change pattern been replaced?")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in callbacks:
                reruns = [d for d in ast.walk(node)
                          if isinstance(d, ast.Attribute) and d.attr == "rerun"]
                with self.subTest(callback=node.name):
                    self.assertEqual(reruns, [], "st.rerun() inside a callback raises")


class UndoBarOrderingTests(unittest.TestCase):
    """_undo_bar's key-clearing must run before anything on the page draws
    a widget that mirrors config state, or an Undo click's own rerun
    redraws that widget with the STALE pre-undo session-state value
    before the clearing ever takes effect. Proven live: when
    _routing_section (which draws the pack-editing multiselect) ran
    before _undo_bar, clicking Undo correctly reverted the FILE
    immediately, but the multiselect kept showing the just-detached pack
    until an unrelated page reload cleared it -- the write was right,
    the redraw was one rerun behind it."""

    def test_undo_bar_runs_before_routing_section_in_configure_page(self):
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        func = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "configure_page")
        calls = sorted(
            (node.lineno, node.func.id) for node in ast.walk(func)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in ("_undo_bar", "_routing_section"))
        self.assertEqual(
            [name for _lineno, name in calls], ["_undo_bar", "_routing_section"],
            "_undo_bar must run before _routing_section in configure_page, "
            "or a widget mirroring config state (see _rule_packs_editor) "
            "draws stale on the very rerun that was supposed to fix it")


class UndoClearsEveryConfigMirroringWidgetTests(unittest.TestCase):
    """_undo_bar drops the session state of every widget that mirrors the
    config file, by key prefix. A widget added later whose prefix is not
    in that tuple survives an Undo showing the value that was just undone
    -- and the next interaction writes THAT back, which is the silent
    re-corruption the whole apply-on-change design exists to prevent.

    The checks table is the live case: it is an st.data_editor holding
    every check's on/off state and numbers, so an Undo that restored the
    file while it kept its pre-undo cells would offer to re-apply them."""

    def _cleared_prefixes(self):
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        func = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "_undo_bar")
        for node in ast.walk(func):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "startswith"):
                arg = node.args[0]
                if isinstance(arg, ast.Tuple):
                    return {e.value for e in arg.elts if isinstance(e, ast.Constant)}
        return set()

    def test_undo_clears_the_checks_editor(self):
        self.assertIn(
            "checks_editor::", self._cleared_prefixes(),
            "_undo_bar does not clear the checks table's session state, so "
            "clicking Undo reverts the config file while the table keeps "
            "showing the on/off states and numbers that were just undone")

    def test_every_cleared_prefix_is_still_used(self):
        """The inverse: a prefix left behind after its widget was deleted
        reads as coverage that no longer exists. `chk::` outlived the
        per-check Enabled toggle by exactly one refactor."""
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            source = f.read()
        for prefix in self._cleared_prefixes():
            with self.subTest(prefix=prefix):
                self.assertGreater(
                    source.count(prefix), 1,
                    f"_undo_bar clears {prefix!r} but no widget uses it")


class DenyPolicyRendersItsOwnOptionsTests(unittest.TestCase):
    """A ruleset option belongs to a check (CHECK_OPTIONS, edited in that
    check's row) or to the deny policy itself. The policy-level ones had
    NO control anywhere: block_flag_count_threshold -- the count at which
    a write is denied, the single most consequential number in the
    product -- was rendered only as a formatted number inside the policy
    sentence, as read-only markdown.

    test_check_text.py's own option-coverage test accepted that sentence
    as proof the option was reachable, which is why nothing caught it:
    the option WAS shown, it just could not be changed. codewatch made it
    visible from the outside -- ten checks, an empty options column on
    every row, because its only option is this one.

    So _deny_policy must render a control, not only prose."""

    def test_deny_policy_renders_a_control_for_policy_level_options(self):
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        func = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "_deny_policy")
        called = {node.func.id for node in ast.walk(func)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertIn(
            "_inline_policy_control", called,
            "_deny_policy renders the deny-policy sentence but no inline "
            "control for the option named in it, so a policy-level option "
            "like the deny threshold is visible and uneditable -- the "
            "exact state this test exists to prevent returning to")
        self.assertIn(
            "_option_control", called,
            "_deny_policy must keep the fallback control row for a policy "
            "option the sentence does not name -- inline-only coverage "
            "silently drops any option added without a placeholder")

    def test_deny_policy_does_not_hardcode_an_option_name(self):
        """Derived from CHECK_OPTIONS, not a name check. A ruleset adding
        a second policy-level number must be covered on arrival, the same
        way blocks_alone_at generalized off two hardcoded check ids."""
        path = os.path.join(SRC_DIR, "configure.py")
        with open(path) as f:
            tree = ast.parse(f.read())
        func = next(n for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and n.name == "_deny_policy")
        literals = {node.value for node in ast.walk(func)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertNotIn(
            "block_flag_count_threshold", literals,
            "_deny_policy names a specific option, so a ruleset declaring "
            "a different policy-level option would silently get no control")


if __name__ == "__main__":
    unittest.main()
