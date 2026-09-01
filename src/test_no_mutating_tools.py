#!/usr/bin/env python3
"""The MCP surface must stay read-only.

This is a security test, not a style test. The MCP server belongs to the
party the gate constrains: a model calls it. A tool there that can relax
the gate lets that party switch off its own constraint. Three tools used
to do exactly that, and none of them was buggy -- each did what it
documented:

  - add_check(fn_body=...) took a matcher body as a string, which
    core/custom_checks.py writes to a file and loads with
    spec.loader.exec_module(). Model-authored Python then ran inside the
    gate process on every later write.
  - set_checks({<every check id>: False}) took a denying gate to a
    passing one in one call.
  - set_check_config(check_id, action="warn") demoted any single
    blocking check.

The fix was to remove the whole category rather than guard each tool,
because "does this call make the gate weaker?" is not decidable per call:
adding a term to an ALLOW list relaxes the gate while adding the same term
to a DENY list tightens it, and a threshold change cuts both ways. A
categorical rule needs no such judgement, and this test enforces it.

A person still performs every one of these operations, through
stopslop.py or the dashboard. That is the trust boundary the hook already
assumes: whoever can write this repository's files can already run code
inside the gate. See SECURITY.md.

If a new read-only tool is added, add its name to READ_ONLY_TOOLS. If a
new WRITING tool is added, this test will fail, and the failure is the
point -- put the operation on the CLI instead.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import mcp_server
    HAVE_MCP = True
except ImportError:  # the mcp package is optional -- see this file's siblings
    HAVE_MCP = False

# Every tool the MCP server is allowed to expose. Each one answers a
# question about text or config; none of them changes what the gate does.
READ_ONLY_TOOLS = frozenset({
    "lint_text",
    "check_word",
    "list_term_lists",
    "list_path_packs",
    "list_checks",
    "list_check_config",
    "scan_codebase",
    "explain",
    "list_rulesets",
    "get_status",
})

# Names that read as mutations. A tool whose name starts with one of these
# is refused outright, so a future add_pack or set_rules trips this test
# before anyone has to reason about what it does.
MUTATING_PREFIXES = ("add_", "remove_", "set_", "update_", "delete_",
                     "save_", "write_", "enable_", "disable_", "register_")


def _exposed_tool_names():
    """Tool names the server actually publishes.

    Read from the module's own functions rather than from any registry the
    mcp package keeps, so this test still means something if that
    package's internals change shape.
    """
    names = set()
    for name, obj in vars(mcp_server).items():
        if name.startswith("_") or not callable(obj):
            continue
        if getattr(obj, "__module__", None) != "mcp_server":
            continue
        names.add(name)
    return names


@unittest.skipUnless(HAVE_MCP, "the mcp package is not installed")
class ReadOnlyMcpSurfaceTests(unittest.TestCase):
    def test_exposed_tools_are_exactly_the_read_only_set(self):
        self.assertEqual(_exposed_tool_names(), set(READ_ONLY_TOOLS))

    def test_no_tool_name_reads_as_a_mutation(self):
        offenders = sorted(n for n in _exposed_tool_names()
                            if n.startswith(MUTATING_PREFIXES))
        self.assertEqual(offenders, [], f"mutating MCP tools: {offenders}")

    def test_the_three_tools_that_could_switch_off_the_gate_are_gone(self):
        # Named individually so a git blame on a re-added one lands here.
        for name in ("add_check", "update_check", "set_checks",
                      "set_check_config"):
            self.assertFalse(hasattr(mcp_server, name),
                              f"{name} lets a model weaken its own gate")

    def test_no_tool_takes_a_python_body_as_an_argument(self):
        # The add_check hole in one property: nothing here accepts source
        # code, whatever the parameter ends up being called.
        import inspect
        for name in _exposed_tool_names():
            params = inspect.signature(getattr(mcp_server, name)).parameters
            for param in params:
                self.assertNotIn(
                    "body", param,
                    f"{name}({param}=...) looks like it takes code")


if __name__ == "__main__":
    unittest.main()
