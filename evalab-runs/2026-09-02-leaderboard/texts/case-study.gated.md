Passes the repo's slopwatch gate, at about 265 words.

## Ravelin Freight, from twelve releases a year to forty a week

Ravelin Freight writes dispatch software for regional trucking companies. For six years they shipped on the last Thursday of the month, and release night ran like a small operation of its own: two engineers stayed late, a third stood by to roll back, and support warned the biggest accounts a day ahead. The cadence itself was not the problem. The problem was what the cadence did upstream of it.

A one-line fix to a fuel-surcharge calculation sat three weeks behind a half-finished redesign of the driver app. Branches drifted apart. On release night nobody could say which of the forty merged changes had caused the latency spike, so a tired team bisected forty commits at 10pm.

They moved to Kestrel CD in March 2024.

The migration took eleven weeks, and most of that was not the platform. It was cutting a 90-minute test suite down to nine, and splitting one database migration path into two so a rollback would not strand half the fleet's records. Eighteen months later, Ravelin deploys about 43 times a week. Median time from merge to production went from 19 days to 35 minutes. Change failure rate dropped from 18% to 5%, and the fix for a bad deploy is now a revert instead of a hotfix branch.

"The surprise was how much of it was cultural," says Dana Oyelaran, who led the migration. "Once shipping stopped being scary, people started shipping smaller things. That did more for our failure rate than any of the tooling."

Release night no longer exists. Nobody misses it.

The customer, platform, quote, and every number here are invented, so they all need replacing before this goes anywhere public. The eleven-week migration paragraph is load-bearing, because case studies that skip the cost read as ads. Tell me the real customer and metrics and I'll refit it.
