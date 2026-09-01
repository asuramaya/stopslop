Details here are invented — swap in your real company, names, and numbers. `[Platform]` is a placeholder for your product.

---

## Ostermann Fluid Systems went from eight releases a quarter to forty a week

Ostermann builds monitoring software for municipal water utilities. Forty engineers, one large Django monolith, and until last year, a release process that ran on a shared spreadsheet and a Thursday night.

"We weren't slow because anyone worked slowly," says Priya Raghunathan, who runs platform engineering. "We were slow because a release was an *event*. Nobody schedules an event twice a week."

The team started with [Platform] in March 2025 on a single service — the alerting API, picked because it was small and nobody was frightened of it. Pipelines were defined in the repo instead of clicked together in a UI, so a broken deploy could be bisected like any other bad commit. Six weeks later they moved the billing service. The monolith took until August.

The numbers as of Q1 2026:

- Deploy frequency: 8 per quarter → 40 per week
- Lead time, merge to production: 11 days → 26 minutes
- Mean rollback: 90 minutes → 4 minutes
- Change failure rate: 14% → 9%

Not everything got easier. Staging had drifted from production for years, and the pipeline surfaced that within a week — Ostermann spent most of April fixing config drift before the rollout could continue. The integration suite, written when it ran twice a month, had to be cut from 51 minutes to 6.

"Deploying often didn't make us careful," Raghunathan says. "Doing it while it was still boring did."
