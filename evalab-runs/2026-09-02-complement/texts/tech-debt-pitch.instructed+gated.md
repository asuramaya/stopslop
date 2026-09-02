# One quarter of engineering time for debt paydown

## What I'm asking for

One engineer-quarter, spread across the team as roughly one day per person per week for twelve weeks, spent entirely on the payments and job-queue subsystems.

## Why now

Our last four sprints each slipped, and for the same reason each time. The payments module has 14 call sites that reach directly into the database rather than going through the service layer, so any schema change requires touching all 14 and re-testing by hand. The October rate-limit change took nine days; the estimate was two.

The job queue has a second problem. It has no dead-letter handling, so failed jobs are retried forever. On 14 August that filled a Postgres table to 40 GB and took the API down for 51 minutes. We patched it with a cron job that truncates the table nightly. That cron job is still the only thing preventing a repeat.

## What we'd do

Consolidate the payments database access behind the existing service interface, then delete the direct call sites. Add dead-letter queue support and remove the cron patch. Backfill integration tests for both, which currently sit at 31% line coverage against a repo average of 68%.

## What we'd give up

Roughly one quarter's worth of feature throughput, deferred rather than cancelled. The bulk-export feature and the second SSO provider would move to Q2.

## How we'd know it worked

I'd track two numbers. Sprint estimate accuracy, currently 58% of stories landing in their estimated sprint, and the count of production incidents traced to these two subsystems, currently six this year. I'll report both at the quarter's end.
