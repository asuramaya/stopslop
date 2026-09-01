# How to contribute

Read this first. This project gates its own text with the tool in this
repository, so a contribution here has one constraint most projects do not
have.

## The gate runs on your contribution

Every Markdown file in this repository routes to a ruleset through
`stopslop.config.json`. This file routes to `ste100`. The root `README.md`
routes to `slopwatch`. Every `.py` file routes to `codewatch` for the code
and to `slopwatch` for the prose inside it.

Run the gate against your own change before you open a pull request:

```
python3 stopslop.py scan <the files you changed>
```

If a file fails a live write, the command exits non-zero. Fix the flags it
names. A note that does not stop the write is still only a note, not a
failure. Read it anyway.

To see the rules that apply to Markdown, read `.claude/skills/ste100/SKILL.md`.

## Run the tests

```
python3 -m unittest discover -s src -p 'test_*.py'
```

That is the whole suite, from the repository root. The gate itself and
`stopslop.py` are pure standard-library Python, so the command needs no
install. The tests in `src/test_mcp_server.py` need the `mcp` package. Without
it, they skip cleanly instead of a failure. To run them for real, install
`requirements.txt` first.

CI runs the same command twice on every pull request: once with no install at
all, and once with `requirements.txt` installed. See
`.github/workflows/tests.yml`.

## Keep the gate free of dependencies

The gate path is `src/pretool_hook.py`, `src/sessionstart_hook.py`, and
`stopslop.py`. These files use only the standard library, and CI has a job
that proves it. Do not add an import outside the standard library to any of
them. The MCP server and the dashboard are the only parts with dependencies.

## Add a ruleset

A new ruleset is a plugin, not a change to the engine. Read
`docs/adding-a-ruleset.md` for the full contract. Every test in
`src/test_contract_doc.py` checks that document against the real code, so a
change to the contract needs a change to both.

## License terms

Your contribution to the code goes out under the MIT license in `LICENSE`.
Do not add third-party content without a NOTICE entry for it. Read `NOTICE`
for the shape of an entry and for the content this repository already
excluded on license grounds.
