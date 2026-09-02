# What we shipped, what broke, what we learned

Twelve months, 214 pull requests to the platform repo, and one incident I still think about.

The big piece of work was the migration off the monolith's job scheduler. We started in March with a two-week estimate and finished in July. The estimate was wrong because we hadn't counted the 40-odd cron entries various teams had added directly to production hosts over five years, none of them in version control. Finding those took longer than rewriting the scheduler. Latency on the checkout path dropped from 340ms at p95 to 190ms over the same stretch. Most of that came from one change: we stopped fetching the full user record on every request when we only needed the account tier. Six weeks of profiling to find a two-line fix.

The June outage lasted 51 minutes.

A config push removed a database connection pool limit, connections climbed until the primary refused new ones, and our health checks passed the whole time because they used a separate pool. We've since made health checks share the application pool, and the postmortem is worth reading if you haven't. On the team side, three people joined, and onboarding time to first merged PR went from eleven days to four, mostly because Priya rewrote the local dev setup into a single script.

Next year we want to finish the observability work we started in Q4. Right now we have good metrics and bad traces, which means we can tell you something is slow but not why. That gap cost us most of the June debugging time. Thanks for a solid year.
