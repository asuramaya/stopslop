# Platform engineering charter

## Why we exist

Engineers here lose too much of the week to work that isn't their product: wiring up CI, chasing deploy failures, guessing at which Terraform module is the current one. We take that work off them. Our customers are the other engineers in this company, and we treat them as customers. They can route around anything we build, and when they do, that's our defect to fix, not theirs.

## What we own

- Build and release pipelines, from commit to production
- The paved road of service templates, runtime environments, and shared infrastructure modules
- Local development environments and the inner loop
- Observability plumbing, including collection, retention, and routing

## What we don't own

Application code. On-call for product services. Product architecture. We supply the defaults and the tooling; teams stay accountable for what they ship on top of them.

## How we work

We build a paved road, not a fence. The golden path is the easiest option available, and a team that needs to leave it can, though we want to hear why. Every platform component is a product with a named owner, a roadmap, and documentation a stranger can follow. Intake happens in the open, and we publish what we've declined along with what we've accepted.

## How we'll know it's working

Median time from a new service's first commit to its first production deploy. Change failure rate. The percentage of services on current templates. And one survey question each quarter that we can't game: if you had a choice, would you still use this?
