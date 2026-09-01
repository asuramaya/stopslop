# Platform Engineering — Team Charter

## Why we exist

Product teams at this company spend too much of their week on work that isn't their product: wiring up CI, guessing at deploy configuration, chasing a staging environment that drifted. We take that work off their plate and make it a paved road instead. When we do our job, a product engineer ships to production on their first day without filing a ticket or asking us anything.

## What we own

- Build and deploy pipelines, from commit to production.
- Environment provisioning and the infrastructure definitions behind it.
- Observability plumbing for logging, metrics, tracing, and the alert routing on top.
- Developer tooling — local setup, test infrastructure, internal CLIs.

We do not own product code, feature-level on-call, or database schema decisions. Where those overlap with our surfaces, we consult; we don't decide.

## How we work

We treat internal teams as customers and our platform as a product, with the same rules: we talk to users before we build, we version our interfaces, and we don't break them without a migration path and notice.

Golden paths are opinionated but never mandatory. A team that needs to step off the path can, and we'd rather hear why than force compliance.

We prefer self-service to tickets, and documentation to tribal knowledge. A request that reaches us twice becomes a tool.

## How we measure

Lead time from merge to production. Change failure rate. Time for a new engineer's first deploy. Quarterly satisfaction survey of the teams we serve.

Reviewed each quarter; amended by team consensus.
