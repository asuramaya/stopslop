# Nobody's job, everybody's problem

"Security is everyone's responsibility" is usually a poster. Then nothing changes. So here's what we actually mean by it.

Two people work on security here. Twelve teams ship code. That math has never worked, and it won't start working if we hire a third person — the gap is structural, not a headcount rounding error.

What shows up in incident reviews is almost never exotic. It's a query built by string concatenation. A token pasted into a config file to unblock a demo on a Thursday. A bucket opened up for debugging and never closed. Every one of those gets caught at the moment it's written, or it gets caught by somebody outside the company.

Three asks.

When you review a PR, ask where the data came from and what happens if it's hostile. You don't need a certification for that question.

When you cut a corner for speed, say it in the PR description. "Hardcoded this key, tracked in PLAT-4412" is fine. Silence is the problem — we can't triage debt we can't see.

When something smells wrong, post in #security-help. No form, no severity rating, no writeup. Forty false alarms cost us an afternoon; one missed real thing costs considerably more. Nobody here has ever caught grief for flagging something that turned out to be nothing.

What we're *not* asking: that you memorize OWASP or become an expert. Threat models, pentests, dependency scanning — ours.

Roughly: we own the tooling and the hard calls. You own noticing.
