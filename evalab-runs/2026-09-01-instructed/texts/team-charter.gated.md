# Platform Engineering — team charter

**Why we exist.** Product teams lose too much of the week to work that isn't their product: standing up a new service, rewiring CI, chasing a failed deploy at 2 a.m. We take that work off them. One team solves each of those problems once, and everyone else gets the answer as a paved road.

**What we own.** Build and deploy pipelines. Service scaffolding, runtime environments from laptop through production, logging and metrics defaults, secrets handling. As a rough test, if a change has to touch every service at once, it's ours.

**What we don't own.** Application code, business logic, and the pager for someone else's service. We supply the tools and the sane defaults; the teams stay accountable for what they ship.

**How we work.** The paved road is optional. Any team can step off it, and we would rather earn adoption than mandate it — a road nobody drives on is our bug, not theirs. We run internal tools the way we would run a product, with written docs, versioned interfaces, deprecation notices carrying real dates, and a named owner for each thing we publish.

**How we'll know it's working.** Empty repo to service running in production, under one day. Rollbacks on fewer than 10% of deploys. Fewer than three platform-caused incidents a quarter. A quarterly survey of every engineer who touches our tooling, published unedited.

**First 90 days.** Inventory what exists, pick the two most-duplicated pieces of infrastructure, and replace them with one supported version. Then ask the teams what hurt next.
