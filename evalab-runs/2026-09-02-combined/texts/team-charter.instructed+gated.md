# Platform engineering charter

## Why we exist

Product teams at this company spend roughly a third of their engineering hours on work that has nothing to do with their product: wiring CI, chasing flaky deploys, re-deriving the same Terraform for the fourth time. We take that work off them and run it once, well.

## What we own

We own the paved road from a commit to production traffic: build pipelines, deployment tooling, the Kubernetes clusters underneath, secrets distribution, and the base observability stack. We own the golden-path templates for new services in Go and TypeScript. We own the on-call rotation for everything in that list.

Not product code. Not product SLOs. Not product on-call. When a service pages at 3am because of a bad query, that page goes to the team who wrote the query.

## How we work

The road is paved, not walled. A team can leave it, and we will help them, but they carry the operational cost of doing so. Anything we require rather than recommend gets written down with the reason attached. We treat internal users as users, which means we ask them and then publish what they said. Every quarter we run the developer survey and post the results unedited, including the parts that make us look bad.

## How we know it is working

We review three numbers monthly. Median time from merge to production. The count of production changes rolled back within an hour. The share of surveyed engineers who say the platform helped them more than it cost them last quarter.

We are aiming first at a service scaffolded and serving traffic in under one working day.
