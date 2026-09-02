# Platform Engineering Charter

## Why this team exists

Product teams at this company spend too much of their week on work that is not their product: wiring up CI, chasing deploy failures, guessing at which Terraform module is the current one. We exist to take that work off them and do it once, properly, for everyone.

## What we own

The paved road from a commit to production. That means build and release pipelines, the deployment tooling, environment provisioning, the shared observability stack, and the templates a new service starts from. We own these as products, with users we can name and a support channel that answers.

## How we work

We treat internal developers as customers who can say no. Nothing is mandatory on day one; adoption is how we find out whether a thing is good. If teams route around our tooling, that is a defect report, not a compliance problem.

We ship small and often. We prefer boring, well-documented technology over anything we would have to explain twice.

## What we are not

We are not a ticket queue for infrastructure requests, and we are not the group that gets paged for every application bug. Where we hold an on-call rotation, it covers the platform itself.

## How we will know it worked

Time from a new engineer's first day to their first merged deploy. Change failure rate. The number of teams who choose our defaults without being asked. We publish these quarterly, including the quarters where they get worse.

Reviewed every six months, or sooner if the scope above stops matching what we actually do.
