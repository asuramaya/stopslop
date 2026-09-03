"""An A/B harness for the question this project never asked itself: does
the gate improve the writing, or only the score?

Named `evalab` rather than `eval` so no import here ever shadows the
builtin.

The experiment, in one paragraph. Take a fixed set of writing prompts.
Run each one through five arms, plus one per competing tool named with `--compare` and one per combined arm named with `--combine`. UNGATED generates once. CONTROL is a
second ungated generation, so its delta is the run's own sampling noise
and a gate delta smaller than that is not a finding. GATED generates,
lints against a subset of the ruleset's checks, feeds any blocking flags
back as a revision request, and repeats until the text passes or the
budget runs out -- the same loop a real session runs against the live
hook. BLIND spends the gated arm's exact compute on a rewrite told only
to rewrite, so a gain cannot be credited to the flags when a second pass
would have done it. INSTRUCTED states the enforced checks' own rules in
the prompt and generates once, which is what a line in CLAUDE.md costs.
Then score every arm with the checks the loop never saw, and with shape
metrics that match no check at all.

Two predictions were under test and the harness returned an
uncomfortable answer to both.

If the gate taught better writing, held-out flags would fall along with
enforced ones. They do not, and they have not in any round with the
signal to measure it.
The gate improves what it is pointed at and nothing else. The
enforced/held-out split exists so that result cannot be talked out of.

If the gate were worth installing, it would have to beat the free thing.
The instructed arm was added last, after three rounds had routed around
it, and it captures about half the gate's effect for one generation and
no install. The gate closes the other half for roughly three times the
compute. Both effects are real; the honest pitch is the trade, not the
72% figure that came from comparing against a rewrite nobody was going to
use instead.

A third question arrived with the multi-turn arm, which applies a
sequence of follow-up edits to a document and scores it after each one.
Real documents are written over many turns and this harness spent its
first fourteen runs measuring first drafts. It found that documents do
NOT get sloppier as they are edited -- two of three models improve --
but that an INSTRUCTION fades: a rule stated once competes with
everything said since, and by the fourth turn it no longer clears
significance, while a gate is unaffected because it reads the text at
the moment of every write.

Every number those rounds produced is replayable from `evalab-runs/` and
recomputable with `stats.py`, which is the point: a published p-value
that lives only in a transcript is not evidence.

Nothing here runs during a gate call. This is an offline instrument.
"""
