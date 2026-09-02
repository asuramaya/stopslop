# The interest payment

Last quarter we shipped the billing rewrite three weeks late. The postmortem named a dozen causes, but the honest one is that the old payment adapter had grown four ways to represent a currency amount, and every change had to satisfy all four. Nobody decided that. It accumulated, one reasonable shortcut at a time, over about five years.

So this month we're writing about what we owe, and what we're paying to keep owing it.

Inside, Priya writes up the currency consolidation that came out of the postmortem, including the migration script that ran for eleven hours and the two rollbacks before it stuck. Marcus makes a case against the "fix it in the next sprint" ticket, with numbers from our own backlog on how long those tickets actually live (median: 412 days). And we're publishing the first pass at a debt register for the payments and identity services, with the criteria we used to rank items, so you can argue with the ranking.

One request. If you have a piece of the system you've been quietly working around, send it to us. We'd rather write about the thing everyone avoids than the thing that's already been fixed.
