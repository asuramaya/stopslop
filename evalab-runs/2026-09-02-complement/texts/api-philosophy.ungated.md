No API reference exists in this repo yet, so I wrote this for stopslop's own public API (the MCP tools and the linter module), which is the natural referent from the working directory. Say the word if you meant a different API and I'll retarget it.

## Design philosophy

Every call returns what a check found, never a verdict on whether the prose is good. The linter reports that `colon_reveal` fired twice in your third paragraph. Whether that matters is yours to decide, and several checks shipped here fire more often on human writing than on generated writing, so the decision is not a formality.

Nothing is hidden behind a mode. `lint_text` resolves a path to a ruleset the same way the commit hook does, so an answer from the API and an answer from the gate agree by construction. If they could disagree, one of them would be misinforming you about a file you are about to write.

Checks are data, not code. A ruleset is a list of check names and thresholds in JSON, and adding one costs the caller nothing. The same property is why you can ask which checks never fire at all — the `decay` command exists because 19 of 31 checks fired zero times across 60,000 words, and an API that cannot be asked that question cannot be audited.

Reads never mutate. No endpoint rewrites your text. Auto-fix is a separate, opt-in path, restricted to mechanical edits a diff makes obvious.
