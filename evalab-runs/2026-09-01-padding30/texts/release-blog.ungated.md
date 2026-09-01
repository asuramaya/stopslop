Draft below — 251 words. Names, numbers, and dates are invented; swap in your real ones.

---

**Fetchkit 2.0**

Fetchkit 2.0 shipped this morning. It is the first release in eighteen months, and it breaks things, so here is what changed and what the upgrade will cost you.

The biggest change: retries are no longer opt-in. Every request goes through a retry policy with exponential backoff and jitter, capped at three attempts by default. In 1.x you had to wire that up yourself, and most people didn't, which is how a flaky gateway turns into a page at 3am. Want the old behavior? Pass `retries: 0`.

We also rewrote the type definitions. 1.x generated types from a hand-maintained schema that drifted from the real API about once a quarter. 2.0 pulls them from the OpenAPI document at build time, so a new endpoint shows up in autocomplete the day it ships.

Smaller items. Request bodies stream instead of buffering, so a 400 MB upload no longer holds 400 MB of heap. Errors carry the raw response. The `legacyAuth` helper is gone.

Bundle size went from 41 kB to 29 kB minified, mostly because we stopped shipping our own URL parser.

The breaking changes are in MIGRATION.md. There are seven. A codemod handles four of them (`npx fetchkit-codemod v2`); the other three need a human, and two of those only bite if you subclassed `Client`.

1.x gets security fixes through June 2027. Nothing else.

`npm install fetchkit@2`

---

Checked against this repo's `slopwatch` ruleset via `lint_text` — passes with no blocking issues.
