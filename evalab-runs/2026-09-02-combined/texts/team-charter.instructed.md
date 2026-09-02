# Charter: platform engineering

## Why we exist

Product teams at this company spend roughly a third of their engineering time on work that is not their product: wiring CI, chasing deploy failures, standing up databases, arguing with IAM. We take that work off them. Our customers are the other engineers here, and our product is the path from a merged commit to running code in production.

## What we own

We own the build and deploy pipeline, the Kubernetes clusters and their surrounding infrastructure, secrets and identity plumbing, the observability stack, and the templates teams start new services from. We do not own product code, product on-call, or product architecture decisions. When those lines blur, we advise and hand the pen back.

## How we work

Paved roads, not gates. A team can go off our road when it has a reason; if enough teams go off it in the same direction, the road was wrong and we move it. We would rather fix the default than write a policy.

We treat internal tooling as a product with real users. That means documentation before announcement, deprecation windows measured in months, and no breaking change that lands without a migration path we have walked ourselves.

We carry our own pager. If the pipeline wakes a product team at 3am, it should have woken us first.

## How to tell if we are working

Time from first commit to a service running in production, currently around three weeks for a new service. Change failure rate on the pipeline itself. Number of teams who have written their own deploy scripts because ours did not fit.

## Review

This charter is revisited every six months, and any engineer here can call it into question sooner.
