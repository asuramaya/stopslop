# Platform engineering charter

## Why we exist

Product teams at this company spend too much of their week on infrastructure they did not want to own. We take that work off their plate. When a team ships a service, they should not write their own deploy pipeline, invent their own logging format, or negotiate with the cloud provider about quotas. Most of what they build in those weeks already exists somewhere else in the company, half-finished, in a repository nobody else can find.

## What we own

We run the build and deploy pipeline, the shared Kubernetes clusters, secrets storage, the observability stack, and the service scaffolding templates. We own the paved road from a fresh repository to production traffic.

## What we do not own

Product code stays yours. We do not write your database migrations or debug your business logic. We advise, we review, we build the tools, and then we get out of your way.

## How we work

We treat product teams as customers, not as tickets. Every quarter we ask each team what slows them down, and we publish what we heard along with what we plan to do about it. We ship the boring version first, because a working template beats a framework nobody adopts. Two numbers tell us whether that is true: median time from commit to production, and the fraction of deploys a product engineer completes without asking us for help. Both go on a dashboard anyone can open.

## On-call

We carry a pager for the platform, not for the services on it. If the cluster is unhealthy, wake us. If your service is unhealthy, we will help you debug it during working hours and we will fix the platform gap that made the debugging hard.

## Escalation

Anyone can file against us. Anyone can ask us to justify a decision. We answer.
