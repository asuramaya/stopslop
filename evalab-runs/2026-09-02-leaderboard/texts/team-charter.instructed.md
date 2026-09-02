# Charter: platform engineering

## Why we exist

Product teams at this company spend a large share of their time on work that has nothing to do with their product: wiring CI, chasing flaky deploys, guessing at Terraform, waiting on someone with the right IAM role. We take that work off them. Our customers are the engineers here, and our product is the path from a merged commit to running code.

## What we own

Build and deploy pipelines. The Kubernetes clusters and the abstractions over them. Secrets, service identity, and environment provisioning. Observability plumbing: metrics, logs, traces, and the alert routing on top. Developer environments and the base images they run on.

We do not own product code, on-call for product services, or architectural decisions inside a product team's domain. When a team's design choice makes our platform hard to serve, we say so and negotiate. We do not veto.

## How we work

Anything we ask a team to adopt has a migration path we write and mostly run ourselves. If adoption requires a wiki page of manual steps, the tool is not finished.

Self-service first. A ticket to us is a bug in the platform; we count tickets and drive the count down.

We publish an interface and hold it stable. Breaking changes get a deprecation window and a named owner on our side.

## How we measure ourselves

Time from commit to production. Change failure rate. Fraction of deploys needing platform intervention. Hours per week teams spend on infrastructure they did not choose. We publish these numbers monthly, including the ones going the wrong way.

## The first six months

Two things: one paved path for a new service that works end to end, and retirement of the Jenkins fleet. Everything else waits.
