**Security isn't a team. It's a habit.**

We have four people on the security team. We have two hundred engineers. Do the math and you'll see why the current arrangement doesn't scale: every finding routes through a queue that four people drain, which means the median time from "someone introduces a hardcoded token" to "someone notices" is measured in weeks. That's not a staffing problem. Adding a fifth reviewer moves the median by days, and the underlying shape stays the same — a bottleneck at the end of the pipeline, catching things that were cheap to prevent and expensive to unwind.

So here's what changes.

Threat modeling moves into design review. Not a separate doc, not a gate — one section in the design you were already writing, answering who can reach this and what happens if they're hostile. Fifteen minutes. Sometimes five.

Dependency and secret scanning runs in CI starting Monday. It fails the build. Yes, that will be annoying in week one. It will be much less annoying than the alternative, which we lived through in March.

And when you spot something outside your area — a service with an open admin path, an old key nobody rotated — file it. You don't need to be sure. We would rather triage twenty false alarms than miss the one real thing because someone assumed a specialist had it covered.

The security team's job is shifting to tooling, review of the genuinely hard stuff, and incident response. The routine catches belong to whoever is closest to the code. That's you.

Questions in #security-eng.
