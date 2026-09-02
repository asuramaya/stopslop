Nomination for Release Engineering team, internal engineering award

I'm nominating the Release Engineering team for their work on the deployment pipeline this year.

In January, shipping a service to production took a 40-minute manual runbook, two approvals, and someone awake in the right timezone. Deploys clustered on Tuesday and Wednesday afternoons because nobody wanted to be the person who broke Friday. Rollbacks were a rewrite of the same runbook in reverse, and they took longer than the deploy did.

The team rebuilt it in stages rather than all at once, which is the part I want to call out. They started with rollback, since that was what made everyone afraid of the deploy, and only then automated the forward path. Median deploy time is now 6 minutes. Rollback is one command and completes in under 90 seconds. Deploy frequency went from 11 a week to 74, and change failure rate dropped from 9% to 4% over the same period.

What I appreciate most is that they did the unglamorous half: they sat with three teams during their first pipeline migrations, took the complaints seriously, and fixed the ergonomics that annoyed people even when nothing was technically broken.

Adoption is at 31 of 34 services. The remaining three have dates.
