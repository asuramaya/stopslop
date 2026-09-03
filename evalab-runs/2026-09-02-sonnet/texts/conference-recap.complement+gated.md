Our team spent last week at AppSec Village. The sessions that stuck were the ones about how attackers move once they're inside, not how they get in.

The keynote on lateral movement in Kubernetes clusters changed how we think about our own network segmentation. The speaker walked through a real incident where a compromised sidecar container let an attacker reach a payments database three hops away. Namespace isolation looked strict on paper but had one shared service account nobody had audited in two years. We're pulling our service account list this week to check for the same gap.

A talk on secrets management convinced us to move faster on rotating the API keys we've had sitting in environment variables since the migration. The presenter showed how a single leaked key in a public gist led to a six-figure cloud bill within four hours, because nothing was scoped and nothing expired. That kind of failure costs almost nothing to prevent and a lot to clean up after.

We also sat in on a panel about incident response communication. The panelists agreed that most postmortems fail not because the technical fix is wrong but because the writeup buries the timeline under jargon nobody outside the team can follow. One panelist argued that if a new hire can't read your postmortem and understand what happened, you should rewrite it.

We came back with three follow-ups. We're auditing shared service accounts, setting expiration on all API keys by end of quarter, and rewriting our postmortem template around a plain timeline.

None of this required new tooling. It required looking at what we already had and asking why it was configured that way.
