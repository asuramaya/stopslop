## 2026 in review

We shipped less this year than last, on paper. Three major releases instead of five. But two of those releases replaced systems that had been quietly failing for a year — the payments retry logic and the search indexer — and both had run in production for six months by December without a single rollback. That's the number that matters, not the release count.

The migration off the old queue system took longer than planned: nine weeks instead of the four we scoped. The delay came from data we hadn't accounted for — about 40,000 jobs stuck in a state the old system never surfaced. We found them because Priya wrote a script to audit the dead-letter queue, something nobody had asked for. That script now runs weekly.

On-call load dropped from an average of 11 pages a week in January to 3 by November, mostly from fixing root causes instead of restarting services. The postmortem backlog is empty for the first time since we started tracking it.

We also lost two people to other teams and didn't backfill either role until Q4, which meant slower code review turnaround for most of the year. That's worth naming plainly, since it shaped what didn't get done: the API versioning work sat untouched from March to October.

Next year: finish the versioning work, get the deploy pipeline under ten minutes (it's at 22 now), and keep the on-call number where it is.

Thanks to everyone who filed a bug instead of just working around it. Those reports are most of why this list is short.
