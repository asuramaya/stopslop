**Kessler Freight: from six-week releases to forty deploys a week**

Kessler Freight's billing team used to ship on a six-week train. If your change missed the Thursday cutoff, you waited until mid-October. That's how a two-line fix to a fuel-surcharge rounding bug sat in a branch for thirty-one days in early 2024, quietly overbilling about 900 customers by pennies a load.

They moved to Harbor CD in March 2024. The migration wasn't clean. Their test suite took 52 minutes, which made per-commit pipelines useless, so the first two months went into cutting that down (parallel test shards, a mock for the carrier-rate API that had been hitting a partner's staging environment). Nobody enjoyed that part.

Now the billing service deploys 40 to 45 times a week. Median time from merge to production is under nine minutes.

"The thing that changed wasn't speed, honestly," says Priya Raghunathan, who runs the platform group. "It's that a deploy stopped being an event. We used to have four people on a bridge call. Now I find out we shipped because Slack told me."

Change failure rate went from roughly 18% of releases needing a hotfix to 4%. Smaller batches, easier to find the culprit.

Kessler still runs monthly windows for the mainframe interchange that talks to their older warehouse systems. Some things you don't touch. And their fraud-scoring service is deliberately gated behind a human approval step, because a bad model rollout there costs real money.

Forty deploys a week, one six-week train still running in the corner. Both true.
