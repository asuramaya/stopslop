# Charter: Platform Engineering

We exist because six product teams were each writing their own deploy scripts, and four of those scripts had the same bug in the rollback path. That's it. That's the origin story.

What we own: the build pipeline, the Kubernetes clusters in us-east-1 and eu-west-1, secrets distribution, and the golden paths for shipping a service from empty repo to production. Not owned by us: your application code, your database schema choices, your on-call rotation. We'll help. We won't take it.

Our test for whether a thing belongs to us is boring but useful. If more than two teams need it and getting it wrong hurts everyone, we build it once. If one team needs it, they build it and we review.

A word on what we're not. We're not a ticket queue. Filing INFRA-1284 and waiting nine days is the failure mode we were created to kill. Self-service first, humans as escape hatch.

We measure ourselves on three things this quarter: median time from commit to production, the number of teams who can deploy without asking us anything, and how often we page someone at 3am. The third number is currently eleven per month. I'd like it under four by December.

Some of this will be wrong. Platform teams drift toward building the elegant abstraction nobody asked for, and I don't have a great defense against that except asking loudly and often whether anyone is actually using the thing we shipped last month.

Ask us anything in #platform-eng. We answer fast.
