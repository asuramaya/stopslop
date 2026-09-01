"""An A/B harness for the question this project never asked itself: does
the gate improve the writing, or only the score?

Named `evalab` rather than `eval` so no import here ever shadows the
builtin.

The experiment, in one paragraph. Take a fixed set of writing prompts.
Run each one twice. The UNGATED arm generates once and stops. The GATED
arm generates, lints against a subset of the ruleset's checks, feeds any
blocking flags back as a revision request, and repeats until the text
passes or the iteration budget runs out -- the same loop a real session
runs against the live hook. Then score BOTH arms with the checks the
gated arm never saw, and with shape metrics that match no check at all.

The prediction under test is the uncomfortable one. If the gate teaches
better writing, held-out flags fall in the gated arm along with enforced
ones. If it teaches nothing but avoidance, held-out flags sit still while
enforced flags collapse, and the gated arm's own iteration count is the
price paid for the illusion. The harness is built to be able to return
that second answer, and the enforced/held-out split exists so the result
cannot be talked out of.

Nothing here runs during a gate call. This is an offline instrument.
"""
