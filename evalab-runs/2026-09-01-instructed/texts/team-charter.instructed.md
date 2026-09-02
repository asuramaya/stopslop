# Platform engineering team charter

## Why we exist

Every product team here has built its own deploy pipeline, its own secret storage, and its own way of getting a Postgres instance. That duplication costs us roughly two engineer-weeks per new service, and it means a security fix has to land in eleven places. We exist to make the shared path the easy path.

## What we own

We own CI/CD, the internal developer portal, Kubernetes cluster operations, secret management, and the observability stack. We own them end to end: design, on-call, and deprecation. If a product team is paged at 3am for something in that list, the page was misrouted.

## What we do not own

Application code, product SLOs, and database schema decisions stay with the teams that write them. We supply the tools and the defaults. We do not approve designs or gate releases.

## How we work

Paved roads, not walls. A team can go off-road, and we will help them, but they carry the operational cost of that choice.

We treat internal users the way we would treat paying ones: intake through a single queue, a response within one business day, and a public roadmap.

Anything we ask a team to do twice, we automate.

## How we know it is working

Time from empty repository to production deploy, measured quarterly. Today it is nine days. Our target for Q2 is under one day.

Change failure rate and mean time to restore across services on the paved road, compared against those off it. If the paved road is not measurably safer, it is not paved.
