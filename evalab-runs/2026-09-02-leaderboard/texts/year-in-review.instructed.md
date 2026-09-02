# The year in review

We shipped 41 releases this year. Four of them we had to roll back within an hour, and one of those took a weekend to untangle. That ratio is roughly what it was last year, which is the part worth talking about.

The migration off the legacy job runner took eight months instead of the three we scoped. The estimate was wrong because we counted the services that called it and not the cron jobs that called those services. Twenty-two of those turned up after we thought we were done. Nobody was surprised by the pattern, only by the number.

Query latency on the search path went from 340ms at p95 to 95ms after Priya's index rewrite in June. That number has held through two traffic peaks since, including the September spike when signups tripled over four days.

We hired three engineers and lost one. Onboarding time to first merged PR dropped from eleven days to four, mostly because Dev spent two weeks writing the local setup script that everyone had been meaning to write since 2023.

Things we said we would do and did not: retire the second Postgres cluster, get integration test runtime under ten minutes (it's at 26), document the billing service. The billing service one has now rolled over three years running.

Next year we're taking on fewer parallel tracks. Two large projects at a time instead of five. We'll find out in twelve months whether that was the constraint or whether we just liked the sound of it.
