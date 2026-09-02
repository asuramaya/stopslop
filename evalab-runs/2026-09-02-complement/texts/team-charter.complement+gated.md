# Platform engineering charter

## Why we exist

Product teams at this company spend too much of their week on work that is not their product: wiring up CI, guessing at Kubernetes manifests, chasing a broken staging deploy, waiting three days for a database. We own that work so they don't have to. Our customers are the engineers here, and our product is the path they take from a commit to production.

## What we own

- The build and deploy pipeline, from pull request to production rollout.
- Clusters, networking, secrets, and managed data stores.
- The plumbing for metrics, logs, traces, and the alert routing on top of them.
- Developer environments and the tooling that provisions them.

We do not own product code, product on-call, or product architecture decisions. When we have an opinion there, we bring it as advice.

## How we work

We build paved roads, not gates. A team that wants to step off the road can, and keeps its own pager when it does. Anything we require, we automate, and if we cannot automate it we drop the requirement.

Every service we run has a documented owner and a runbook before it takes traffic. We treat our own tooling as production: versioned, tested, and reviewable.

We measure ourselves on lead time from merge to production, change failure rate, and time to restore. We publish those numbers monthly whether or not they flatter us.

## Our promises

Answer requests within one business day. Give a real date or a real no, never silence. When we break something, we say so first, in writing, before anyone has to ask.
