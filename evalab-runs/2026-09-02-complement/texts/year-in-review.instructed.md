# The year the queue stopped being scary

Twelve months ago the on-call rotation was three people who understood the ingest pipeline and a wiki page that lied. We finished the year with eleven people rostered and a runbook that survives contact with an actual incident.

The migration off the monolith's job scheduler took from February to August, longer than the six weeks we scoped. Most of that overrun was one thing: retry semantics nobody had written down. Jobs that failed at stage three were being replayed from stage one, and a handful of downstream partners had built their reconciliation around that accident. Untangling it meant a quarter of conversations with people outside the team before we could delete a single line.

Numbers worth keeping. Median job latency went from 4.2s to 900ms. The p99 barely moved, which is the honest part of the story and the thing we're carrying into next year. We cut 31,000 lines and added 12,000. Deploy frequency went from twice a week to roughly nine times a day.

What did not go well: we shipped the new dead-letter UI without asking support what they needed, and rebuilt half of it in October. Anna's postmortem on that is the best internal doc we produced all year, and it's short.

Next year the plan is narrower. Get p99 under two seconds, finish deprecating the v1 API (37 callers left, down from 400), and hire two more people onto the platform side so the rotation stops depending on Marcus being awake.
