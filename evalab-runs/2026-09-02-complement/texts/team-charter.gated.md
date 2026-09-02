# Charter — platform engineering

## Purpose
The platform team exists so product teams can ship without each of them rebuilding the same infrastructure. We own the paved road, meaning the default way to build, test, deploy, and run a service here.

## What we own
- CI/CD pipelines and the release path to production
- Runtime environments, including the clusters and their base configuration
- Shared observability — logs, metrics, traces, and the alerting on top of them
- Developer tooling such as local environments, service scaffolding, and internal libraries
- Identity, secrets, and the access guardrails around them

## How we work
We treat the platform as a product and product teams as our customers. We publish interfaces and then support them. We take requests through a backlog rather than hallway asks. We deprecate on a schedule, with notice.

We build paths, not walls. A team can step off the paved road, but it then carries the operational load itself. We won't block that choice; we will document what it costs.

## What we are not
We are not a ticket queue for work a team can do itself, and we are not the on-call rotation for other people's services. We run the platform. Each team runs what it builds on top.

## How we measure ourselves
Lead time from commit to production. The share of services on the paved road. Platform availability against its stated SLOs. A quarterly read on how developers actually experience the tooling.

If those numbers don't move within two quarters, the problem is this charter, and we will rewrite it.
