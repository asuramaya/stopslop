Fenwick Logistics ships route-planning software to about 400 freight brokerages. Until early 2024, releases went out every six weeks, on a Thursday night, with four engineers on a call and a rollback plan nobody wanted to use.

The bottleneck was not the team's willingness to ship. It was that a full test run took 90 minutes on shared hardware, and the staging environment was hand-built, so any failure could plausibly be the environment rather than the code. Engineers batched changes to avoid paying that cost twice, and batching made each release riskier, which justified more review, which stretched the cycle further.

They moved to a continuous delivery platform in March 2024. The migration took eleven weeks, most of it spent not on the tooling but on splitting a test suite that assumed a single shared database. Two engineers did that work full time. The platform handled ephemeral environments per pull request and progressive rollout by traffic percentage.

Deploy frequency went from roughly 8 per year to 31 per week, measured across the four services in the main repo. Median lead time from merge to production is now 22 minutes. Change failure rate rose slightly, from 4% to 6%, but mean time to restore dropped from 3 hours to 14 minutes, because a bad rollout now affects 5% of traffic and reverts with one command.

"We stopped negotiating about what goes in the release," says Dana Okonkwo, who runs platform engineering there. "There isn't a release anymore. There's just Tuesday."

The team still holds a weekly review for schema migrations, which they have no plans to automate.
