Senior backend engineer

Payments platform team, Chicago or remote (US time zones)

We process about 4 million card and ACH transactions a month for roughly 900 business customers. The ledger, the settlement pipeline, and the reconciliation service are Go and Postgres, running on ECS. Some of it was written in 2019 by three people in a hurry, and it shows.

You would own the settlement pipeline. Right now it runs as a nightly batch that takes 40 minutes and fails loudly about once a fortnight when an upstream bank file arrives malformed. We want it incremental, restartable, and correct under partial failure. That is the first six months of the job.

What we need you to have done before: built systems where money movement had to balance, worked with Postgres past the point where the query planner became your problem, and debugged production incidents at 3am without a runbook. Six or more years total. Go is preferable, but we have hired strong Java and Python people and they were productive in a month. We are less interested in distributed systems theory for its own sake, and we will not hire someone whose instinct is to rewrite rather than repair.

Compensation is $185,000 to $215,000 base, plus equity. We publish the band because we do not negotiate off it. Benefits cover medical, dental, and vision at 100% for you and 75% for dependents.

You will do a 45-minute call with the hiring manager, then a two-hour paid technical session on a real bug from our tracker, then a conversation with two engineers on the team. Three weeks start to finish. Apply at careers.example.com/be-senior. No cover letter.
