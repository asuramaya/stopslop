# Security model

Read this before you rely on stopslop for anything. The short version: it
is a speed bump for a careless writer, not a barrier against a determined
one. Most of this page describes what it does NOT defend against.

## What the gate is

A `PreToolUse` hook that intercepts `Write`, `Edit`, and detected `Bash`
file writes in a Claude Code session, and can deny one before it reaches
disk. Plus a `pre-commit` hook that judges the staged tree.

## What it does not defend against

**Any agent that can run shell commands.** A shell is arbitrary code
execution. Such an agent can write files with `python3 -c`, `sed -i`, or a
text editor, none of which the hook sees. It can also disable the hook
outright. If the model has Bash, treat the gate as advisory.

**Bash writes in general.** Detection is deliberately conservative. It
misses `printf` with real format arguments, and a multi-line `cat >>`
append with no heredoc, among others.

**A commit.** `git commit --no-verify` skips the pre-commit hook. That is
git's own flag, and no hook can refuse it.

**Text that is clean and empty.** Every check tests a surface property of
the text. A writer that avoids the flagged constructions and says nothing
passes. A blocking gate makes this worse than a warning would, because it
gives a model a tight loop to iterate against until the checker goes
quiet. Nothing here measures whether prose is worth reading.

The honest description of the gate is "a linter, plus a hook that catches
the paths a careless writer actually uses." That is real value against
ordinary sloppiness. It is not a security boundary, and any threat model
that treats it as one is wrong.

## The trust boundary

**Anyone who can write this repository's files can already run code
inside the gate.** The hook imports this repository's own Python on every
call. A person editing `src/` has code execution by definition. That is
not a vulnerability, it is the premise, and it is why the guardrail on
ruleset loading is "fail loudly at load time" rather than any attempt at
sandboxing.

Custom checks are the same premise applied to a smaller file. A check
saved under `.claude/stopslop/custom_checks/<ruleset>/<check>.py` is real
Python, loaded with `spec.loader.exec_module()` and run in the gate
process. That is the feature working as intended: a project author writes
a matcher, and the gate runs it. Review these files the way you review
anything else in the repository. They are not gitignored, on purpose.

## Where that boundary was drawn wrong, and the fix

The MCP server used to expose writing tools: `add_term`, `add_check`,
`add_ruleset`, `set_checks`, `set_check_config`, and others. Each did what
it documented. Together they handed the party the gate constrains a
complete off-switch, three ways:

1. `add_check(fn_body=...)` took a matcher body as a string. The gate then
   ran model-authored Python in its own process on every later write. A
   text gate had become an arbitrary code-execution surface.
2. `set_checks({<every check id>: False})` turned a denying gate into a
   passing one in a single call. Measured against a real ruleset, not
   theorized.
3. `set_check_config(check_id, action="warn")` demoted any single
   blocking check.

The defense in the source at the time was that this granted nothing new,
since repository write access already implies code execution. That
reasoning holds for a person and fails for a model. The gate exists
because the model is not fully trusted, so a surface that lets the model
relax the gate inverts the privilege it was built to hold. Worse, it
inverted it exactly in the configuration where the gate is load-bearing:
an agent with `Write`/`Edit` and MCP but no Bash has no other route to
code execution, and `add_check` was one.

**The fix: the MCP server is read-only.** Fifteen writing tools were
removed; ten reading tools remain. Every operation those tools performed
is still available through `stopslop.py` and the dashboard, which a person
drives.

The rule is categorical rather than per-tool, because "does this call make
the gate weaker?" has no per-call answer. Adding a term to an *allow* list
relaxes the gate. Adding the same term to a *deny* list tightens it. A
threshold change cuts both ways. A rule that needs a judgement on every
call fails the first time someone gets the judgement wrong;
`src/test_no_mutating_tools.py` enforces the categorical one, and fails if
a writing tool is ever added back.

## The dashboard

It binds `127.0.0.1` only, so it is not reachable from the network. It has
no authentication, and it can write config and custom-check code. Any
local process on the machine can therefore drive it. On a single-user
machine that matches the trust boundary above. On a shared or multi-tenant
host, do not run it.

## Reporting

Open an issue. This is a prototype with no users, no release, and no
security-response commitment. Do not use it where a failure would matter.
