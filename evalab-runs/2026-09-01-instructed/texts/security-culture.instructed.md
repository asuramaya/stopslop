# Security is a shared job now

Starting this quarter, security review stops being a gate the security team holds and becomes part of how every team ships.

Here is what changed and why. Last quarter we had 41 findings that reached the security team's queue. 33 of them were things the authoring team could have caught: a hardcoded credential in a test fixture, an endpoint that skipped the auth middleware, three separate cases of user input reaching a SQL string. Average time from filing to fix was 19 days, mostly spent waiting for someone with context to become available. The security team is four people supporting 140 engineers. That queue is never going to get shorter by adding reviewers to it.

So the model shifts. Each team names a security contact — not a new job, a rotation. That person runs the threat-model checklist when a design doc touches auth, data storage, or anything network-facing, and they get a half-day of training in October to make the checklist mean something.

The security team's work moves upstream: tooling, training, and the hard reviews that actually need specialist judgment. They will still review anything touching payments, PII, or the auth service. Those stay mandatory.

Two things this is not. It is not a headcount cut to the security team. And it is not permission to skip review because you looked at your own code and it seemed fine.

Kickoff sessions are on the calendar for the week of September 14, one per org. Bring the thing you have been meaning to ask about.
