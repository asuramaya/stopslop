# Charter: Platform Engineering

## Why we exist

Product teams at Meridian wait an average of nine days between "code is ready" and "code is in production." Most of that time goes to hand-rolled CI configs, ticket queues for staging databases, and three incompatible ways to get secrets into a container. We own that gap.

## What we own

- The deploy path: CI templates, build runners, release pipelines, rollback.
- Runtime infrastructure: Kubernetes clusters, ingress, service mesh, secrets.
- Developer environments: local setup, ephemeral preview environments, test data.
- Observability plumbing: metrics, logs, traces, and the alert routing on top of them.

We do not own product code, on-call for product services, or feature-level SLOs. Those stay with the teams that write the features.

## How we work

We build paved roads, not gates. A team can go around us; if enough teams do, our road is wrong and we fix it rather than mandate compliance.

Every capability ships as self-service with docs before we announce it. If a request requires a Slack message to us, it is a bug in the platform.

We take support in a weekly rotation, one person at a time, so the other five keep building. Anything asked three times becomes documentation or automation.

## How we measure

Four numbers, reviewed monthly: median time from merge to production, preview environment provision time, change failure rate, and platform-caused incident minutes. We publish them whether they moved or not.

## First six months

Cut merge-to-production from nine days to under one. Retire the four legacy Jenkins instances. Give every product team a preview environment on pull request.
