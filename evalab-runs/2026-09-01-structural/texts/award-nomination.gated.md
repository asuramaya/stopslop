Nomination for [Team Name], for the deployment overhaul

I'm nominating [Team Name] for their work rebuilding how we ship code.

Before this year, a release took [X hours] and needed [N] people awake for it. The runbook was thirty steps long, and about half of them were "check with someone." Rollbacks meant reversing those steps by hand, usually at a bad hour. Most of us had stopped deploying on Fridays, which quietly cost us a day of throughput every week. The team replaced that with an automated pipeline, so now one merge to main triggers a staged rollout with health gates, and a rollback is a single command instead of a procedure. They did it incrementally, migrating [service] first and keeping the old path alive until people trusted the new one. Nobody had to stop shipping while it happened.

Deploy time has since dropped from [X] to [Y], and the failed-deploy rate is down [Z]%. We run [N] deploys a week where we used to do [M]. Friday deploys are normal again.

What I want to recognize is not only the result but the way they got there. They fixed infrastructure that wasn't theirs, took no credit in standups, and wrote documentation good enough that the rest of us stopped asking them questions.
