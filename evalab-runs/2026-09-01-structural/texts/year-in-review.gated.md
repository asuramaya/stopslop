What we shipped, and what shipped us

We started the year with one on-call rotation and a queue-depth graph nobody trusted. Both are gone.

The migration off the legacy job runner took seven months — three longer than we told you it would. Nobody enjoyed that. What replaced it has run 4.2 million jobs since April with no manual intervention, and the retry logic is now something a new hire can read in an afternoon. The rest of the numbers held up too. p99 checkout latency went from 1.8s to 410ms, mostly one N+1 query and one cache we should have added in 2023; we went from deploying twice a week to deploying about forty times a day; median PR review time dropped from 26 hours to 4.

The parts that didn't work are worth saying out loud. We tried to standardize on one frontend test setup in Q2 and quietly gave up in Q3. Two teams still run their own. That's fine — better to admit it than keep the migration doc open another year, collecting stale checkboxes.

Ada rewrote the schema linter over a long weekend; it has caught 61 breaking changes before they reached staging. Marco's incident review template is now used by three other orgs. Neither was on a roadmap.

Next year we're doing fewer migrations and more deleting. There are 40k lines in the repo that no request has touched since 2024, and we know which ones.

Thanks for a hard, good year. Go take the holidays.

One note before this circulates. The names, metrics, and dates in here are placeholders — send me the real ones, or the team's retro notes, and I'll swap them in.
