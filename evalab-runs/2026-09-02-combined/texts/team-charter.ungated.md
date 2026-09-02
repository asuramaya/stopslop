I don't have your org's specifics, so this is written to be filled in — swap the bracketed bits.

---

# Charter: Platform Engineering

## Why we exist

Product teams at [Company] spend too much of their week on infrastructure that nobody wants to own. We take that work off them. Our customers are the engineers here, and our product is the path they take from a commit to running code.

## What we own

CI and build tooling, deployment pipelines, the Kubernetes substrate, observability plumbing, and the internal developer portal. We own the defaults. Teams can go off the paved road when they have a reason, but they carry the pager when they do.

## What we don't own

Application code, product decisions, and on-call for services we didn't write. We are not a ticket queue for one-off infra requests. If we're doing the same manual task a third time, it becomes a self-service capability instead.

## How we work

We treat internal tooling like a product: interviews before roadmaps, adoption as the measure of success, deprecation with notice and a migration path. Everything we run has an owner, a runbook, and an SLO. We publish our roadmap and our failures.

## How we'll know it worked

Time from first commit to production for a new service. Change failure rate. Percentage of deploys that need no help from us. If those numbers move and engineers stop thinking about us, we've done the job.

## Our first ninety days

Inventory what exists, interview ten engineers across four teams, pick the two worst bottlenecks, and fix one of them end to end.
