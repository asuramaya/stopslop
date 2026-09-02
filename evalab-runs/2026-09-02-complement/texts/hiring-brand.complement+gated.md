# How we work

We ship small changes often. A typical pull request touches a few hundred lines, gets reviewed within a day, and goes to production the same week. Nobody sits on a six-month branch here.

Every engineer owns their code in production. You write it, you deploy it, you get paged when it breaks at 2 a.m. We make that bearable by rotating on-call weekly across a team of eight, and any page that fires twice becomes a ticket before the next rotation. The goal is a rotation you can hand off without a briefing.

Design happens in writing. Anything that changes an API contract or adds a dependency starts as a two-page document, circulated for comments, decided within a week. We keep the archive going back to 2019, so when someone asks why the billing service talks to Postgres instead of the event bus, the answer has a date and an author on it. That archive has settled more arguments than any meeting we have ever held, and it saves new hires from relitigating decisions that were made carefully the first time.

We pay down debt on a schedule: one week per quarter, teams pick their own cleanup work with no feature commitments. Last quarter that got us off a Python runtime that had been out of support for a year.

Disagreement is normal, and it gets resolved by the person closest to the problem rather than the person with the longest tenure. If a senior engineer and a new hire read the same trace differently, we run the experiment and let the result decide, which is usually faster than arguing about it. So we hire people who can explain their reasoning to someone outside their specialty. Most of the hard problems here sit between teams, and the fix usually requires convincing somebody in a different room that your read of the system is right.
