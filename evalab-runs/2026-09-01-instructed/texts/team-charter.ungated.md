**Platform Engineering — Team Charter**

**Why we exist**

Product teams currently spend a large share of their time on work that isn't their product: wiring CI, guessing at Kubernetes manifests, chasing secrets, waiting on environments. We exist to absorb that work once, well, so it doesn't get re-solved badly forty times.

**What we own**

The paved road from commit to production: build and CI templates, deployment tooling, environment provisioning, observability defaults, and the developer-facing interfaces to all of it. We own the road's condition, not the traffic on it. Application code and on-call for application behavior stay with the teams that write it.

**How we work**

We treat the platform as a product and our engineers as customers who can leave. That means we ask before we build, we publish a roadmap, and we measure adoption rather than assume it. Golden paths are opinionated and optional — teams may go off-road, but they carry the pager when they do.

We prefer boring, well-documented tools over interesting ones. We ship in small increments. We write things down.

**What we will not do**

Act as a ticket queue for one-off infrastructure requests. Approve architecture we didn't help design. Take ownership of a system by accident because nobody else volunteered.

**How we'll know it's working**

Lead time from merge to production. Time for a new engineer to deploy their first change. Percentage of services on the paved road. Change failure rate. We publish these quarterly, including the quarters they get worse.

This charter is reviewed every six months and is expected to change.
