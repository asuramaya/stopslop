# Northgate Logistics cut its release cycle from six weeks to daily

Northgate Logistics runs freight brokerage software for about 1,400 carriers across the Midwest. Until early 2024, its engineering team shipped on a six-week cadence: a code freeze, a two-day manual regression pass, and a Saturday-night deploy window that three people had to be awake for.

The bottleneck was not the code. It was the coordination. Each release bundled roughly 60 merged pull requests, so when something broke, finding the culprit meant bisecting a batch that had been sitting in staging for a month.

Northgate adopted a continuous delivery platform in March 2024 and spent the first quarter doing unglamorous prep work: containerizing two legacy services, replacing a shared staging database with per-branch ephemeral environments, and writing rollback playbooks for the four services that touch payments.

Deploy frequency went from 8 releases per quarter to 340. Median lead time from merge to production dropped from 19 days to 47 minutes. Change failure rate rose slightly, from 4% to 6%, which the team considers a fair trade: a failed deploy now affects one change instead of sixty, and mean time to restore fell from 4 hours to 22 minutes.

"We stopped treating deploys as events," says Priya Raman, Northgate's director of engineering. "Nobody schedules a Saturday anymore. The last three incidents were caught by canary metrics before a customer noticed."

The remaining holdout is the carrier settlement service, which still ships weekly. Northgate plans to bring it onto the same pipeline once its audit logging is rebuilt in Q3.
