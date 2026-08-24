"""stopslop's bespoke local dashboard -- a from-scratch FastAPI + htmx
replacement for the old Streamlit dashboard (src/dashboard.py,
src/configure.py), built alongside it on a separate dev port until
cutover. See docs/webui-migration.md (added at cutover) for the
rationale; the short version: Streamlit had no widget that both selects
and edits a row, its global session state caused a real data-corruption
incident once, and its whole-file-snapshot undo needed a manual
session-state-key-clearing dance this project's own comments documented
as a workaround, not a design. This package is presentation only -- every
read and write still goes through the same core.config/core.terms/
core.checks/ruleset functions the CLI and the hook already use.
"""
