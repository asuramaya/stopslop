Platform Engineering Team Charter

**Mission**
We build and operate the internal infrastructure other engineering teams depend on: deployment pipelines, developer tooling, service infrastructure, and the paved paths that let product teams ship without relearning the same operational lessons.

**Scope**
We own CI/CD systems, internal developer tools, cloud infrastructure and its provisioning, observability (logging, metrics, tracing), and the standards for how services get built, deployed, and run. We do not own product features or business logic; we own the ground those features stand on.

**How we work**
We treat internal engineering teams as customers. We ship self-service tools and paved paths instead of manual tickets, and we measure success by how much toil we remove from other teams' workflows, not by how much infrastructure we personally operate.

We favor boring, well-understood technology over novel systems, because reliability compounds and outages cost more than the time saved by a clever choice. When we take on complexity, we document why in an architecture decision record.

**On-call and reliability**
We hold a shared on-call rotation for the systems we own. We write postmortems for significant incidents and act on their follow-ups; a postmortem without a completed action item is unfinished work.

**Decisions**
Changes to shared infrastructure (build systems, deployment mechanisms, core libraries) go through a proposal reviewed by the team, with input from affected teams before a change ships broadly. Reversible changes ship fast; irreversible ones (data migrations, breaking API changes) get a second reviewer and a rollback plan.

**Review**
We revisit this charter every two quarters, or sooner if our scope or headcount changes enough to make it stale.
