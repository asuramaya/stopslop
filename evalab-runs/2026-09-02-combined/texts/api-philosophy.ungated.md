Assuming you mean this project's own API (the ruleset contract plus the MCP tools) — here is a draft for `docs/`:

## Design philosophy

Three ideas run through this API and account for most of its surface.

The first is that the gate knows as little as possible about what it gates. A ruleset supplies three functions and three attributes, and nothing else crosses that boundary. You can add a house style, an ASD-STE100 dialect, or a check table for something nobody has written yet, and the hook never learns a thing about it.

The second is that calls return findings, not verdicts. `lint_text` hands back every flag with its offset, check name and ruleset. Whether a flag blocks a write, gets fixed in place, or is merely noted is a routing decision, and routing lives in your config where you can read it.

Third, the defaults are provisional and say so. Thresholds here were calibrated against human prose rather than intuition, and several checks were dropped once measurement showed they fire more often on people than on models. `decay` and `decay --calibrate` print the evidence behind the current numbers. Expect those numbers to move; pin a version if you need them not to.

What the API will not do is rank your writing. It reports whether text carries patterns that mark it as generated, which is a narrower question.
