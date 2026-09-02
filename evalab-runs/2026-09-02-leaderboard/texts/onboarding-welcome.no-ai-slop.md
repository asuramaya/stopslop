# Welcome

Your first pull request merges this week. Not a doc fix. Real code, in a service customers use.

That sounds fast because it is. We deploy about 30 times a day, and the fastest way to learn the system is to change it and watch what happens. Your buddy will pick a small, contained ticket and sit with you while you ship it.

**Today**

Grab your laptop from IT (2nd floor, ask for Priya). Run `./bootstrap` in the platform repo. It takes about 40 minutes and it will fail at least once on the Postgres step. The fix is in the README under "bootstrap failures." If that doesn't work, post in #eng-help.

**This week**

Your buddy owns your first five days. They'll walk you through the deploy pipeline, on-call, and how a request travels from the edge to the database. Meet your manager Wednesday for a 1:1.

**How we work**

Write the design doc before the code when the change touches more than one service. Two reviewers, one of whom knows the area. If a test is flaky, delete it or fix it; don't retry it.

Ask questions in public channels, not DMs. Someone else has the same question and can't find your DM.

You will break something in your first month. When it happens, say so in #incidents, roll back, then write what happened. We don't do blame in postmortems, and we've never fired anyone over an outage.

If you're stuck for more than 30 minutes, that's a signal to ask, not to push harder.
