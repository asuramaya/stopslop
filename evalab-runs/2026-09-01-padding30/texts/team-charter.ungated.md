# Platform Engineering Team Charter

**Why we exist.** Product teams at this company spend too much of their week on work that isn't their product: wiring up CI, chasing a broken deploy, guessing at the right Terraform module, waiting on someone in infra to answer a Slack thread. We take that work off them. Our customers are the engineers here, and our product is the paved road they build on.

**What we own.** Build and deployment pipelines. The service scaffold and the templates behind it. Environment provisioning. The observability stack, including logs, metrics, traces, and the alerting on top. Shared infrastructure primitives such as databases, queues, and caches. We own these end to end, from the interface a developer sees down to the cost line on the bill.

**What we don't own.** Application code and business logic stay with the teams that write them. We don't run other teams' on-call rotations. We won't be a ticket queue for one-off infra requests; if a request comes in twice, we turn it into something self-service.

**How we work.** The paved road is optional but good enough that leaving it is a deliberate choice, and teams that do keep their own pager. We ship in small increments and dogfood everything before it reaches anyone else. Breaking changes get a migration path and a deprecation window, never a surprise.

**How we'll know it worked.** Time from first commit to production for a new service. Change failure rate and recovery time. How often teams reach for the road versus around it. If those numbers stall, the charter is wrong and we rewrite it.
