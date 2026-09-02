# The Year, According to the Backlog

We closed 1,847 tickets. I know that because Priya built the dashboard in February after we spent a whole retro arguing about whether things felt busier than last year. They did. About 30% busier.

The migration off the old billing service took eight months instead of the four we estimated. Marcus found the undocumented cron job in week three that nobody could explain, and we spent two sprints tracing what it touched before we dared turn it off. Everyone who has read that postmortem knows the estimate was optimistic. We wrote down why: we scoped the code, not the surprises.

Three things went better than expected. Deploy time dropped from 40 minutes to 6 after Ana rewrote the test parallelization. On-call pages fell by half, mostly because we stopped alerting on the disk-usage threshold that fired every Tuesday at 3am for no reason anyone could name. And the new hires shipped to production in their first week, which happened because Tomás rewrote the setup docs in January and kept editing them each time someone got stuck.

What we still owe ourselves: the API versioning work slipped three quarters running. Every planning session we agree it matters, and every planning session something louder wins. Next year we either schedule it in Q1 or admit we won't do it.

Thanks for a year of good arguments in code review. Ana's comment on PR #4402, the one with the six-paragraph explanation of why the cache key was wrong, taught me more than any conference talk. Do more of that.
