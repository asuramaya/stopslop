## Security is not the security team's problem

Last month an engineer on Payments spotted a token in a debug log, pulled it, rotated it, and had the fix merged in under an hour. They didn't open a ticket with us first. They told us afterward. That is exactly the behavior we want.

Here is the arithmetic. There are six of us in AppSec and about two hundred and forty engineers shipping code. If every security question has to route through a queue we own, the queue becomes the bottleneck and people learn to go around it. They will. Reviews get skipped at 6pm on a Thursday before a release.

So we are changing where the work sits. Three things, starting this quarter:

**Design docs get a threat section.** Four or five lines: what data does this touch, who can reach it, what happens if the token leaks. If you cannot answer the third one, that is the finding.

**Secrets scanning runs pre-commit, not in CI.** Catching a key after it is in git history means a rotation, not a fix.

**Report weird things in #sec-help without a writeup.** A screenshot and a sentence is enough. Nobody has ever been blamed in that channel and nobody will be.

We are not handing you our job. We still do the threat modeling on the hard systems, the pen test coordination, the incident response. What we cannot do is be in the room for every decision that touches a credential. You already are.

Questions to me or in #sec-help.

---

~255 words. Swap in your real team size, channel name, and quarter — the arithmetic paragraph only lands if the numbers are yours. Linted clean against this repo's `slopwatch` ruleset.
