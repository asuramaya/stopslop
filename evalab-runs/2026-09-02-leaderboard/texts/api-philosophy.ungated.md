You didn't name an API, so I wrote it for this repo's public one (the ruleset/gate contract and the MCP surface), in the README's voice. 197 words, passes `slopwatch` clean.

### Design philosophy

**Small contract, replaceable parts.** A ruleset is three functions and three attributes, and the gate knows nothing else about it. Want different rules? Write a package. You never patch the dispatcher. That constraint is the entire extensibility story, and it is deliberately boring.

**Warn by default, block on defects.** A check blocks only when it catches something wrong — a swallowed exception, a safety instruction with no actor. Everything else warns. Style is a correlate, not a verdict, and the API refuses to pretend otherwise.

**Every claim is checkable.** `explain` returns the wording of the rule that fired, not a score. `lint_text` returns flags with offsets you can point at in the source. Nothing here reports a number you cannot reduce to a sentence in a document you can read.

**No hidden state.** A call is a pure function of text plus config. Same input, same flags, forever. That is what makes the evaluation harness possible at all.

**Published limits.** The gate misses write paths it never sees, overshoots the human band on structural checks, and wins only on the checks it was pointed at. Those limits live in the documentation, with numbers attached.

Draft is at `/tmp/philo.md`. If you meant a different API, tell me which and I'll retarget it.
