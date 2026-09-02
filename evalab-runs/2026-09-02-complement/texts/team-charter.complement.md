# Charter: Platform Engineering

## Why we exist

Product teams at this company spend roughly a third of their time on work that has nothing to do with their product: wiring up CI, chasing flaky deploys, guessing at Terraform, waiting on someone in infrastructure to grant a role. We take that work off them and turn it into paved paths they can use without asking permission.

## What we own

- CI/CD pipelines and the build system
- Kubernetes clusters, and the deployment tooling that sits on top of them
- Observability: metrics, logs, traces, and the alerting that hangs off them
- Developer environments, from laptop setup to preview deploys
- The internal service catalog and the templates that seed new services

## What we do not own

We do not own product code, on-call rotations for product services, or the decision about what a team ships. If a team wants to leave the paved path, they can. They keep the consequences.

## How we work

We treat internal developers as customers, which means we ship things people choose to adopt rather than things they are told to adopt. Adoption is our metric. A tool that nobody uses is a failure regardless of how well it was built.

Every request that arrives twice becomes a self-service capability. We publish what we're building before we build it, and we run a public backlog.

## First-year goals

Cut median time from commit to production below fifteen minutes. Get eighty percent of services onto the standard deployment template. Reduce infrastructure-related pages for product teams by half.

We revisit this charter every six months.
