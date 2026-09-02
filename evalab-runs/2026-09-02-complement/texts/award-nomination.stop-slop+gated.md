I nominate the Release Platform team for the Engineering Excellence Award.

In January, a deploy took 47 minutes and one engineer watching a terminal to make sure it landed. Four people changed that. Priya rewrote the build cache so services with no code changes skip the rebuild. Marcus broke the single pipeline into per-service stages that run at the same time. Dan and Sofia built the rollback path that watches error rates for ten minutes after a release and reverts on its own.

A deploy now takes six minutes. Last quarter we shipped 312 times, up from 84 the quarter before. Twice the rollback fired at 3 a.m. and no one woke up for it.

They did the unglamorous half too. Sofia sat with each of the nine service teams and migrated their configs by hand instead of filing tickets and waiting. Dan wrote the runbook that new hires use in their first week. Marcus spent two months deleting the old Jenkins jobs so nobody would find them later and wonder which system was live.

Ask any engineer here what changed about their week this year and they will bring up deploys. That is the team you want to reward.
