# Three days at ScaleConf, and what stuck

We sent four people to ScaleConf last week. Here's what came back with them.

The infrastructure track was mostly a referendum on Kubernetes complexity. Two separate talks described teams that had migrated off it — one to plain ECS, one to a pair of Hetzner boxes and systemd units. Neither presenter framed it as a rebuke. Both said the same thing: they had adopted the platform for a scale problem they turned out not to have. Our own cluster runs eleven services. We are going to sit with that number for a while.

Priya spent most of her time in the observability sessions and came back annoyed. The vendor booths were selling AI-driven root cause analysis; the practitioner talks were still about cardinality budgets and whether anyone reads the dashboards. The gap between those two rooms was the most useful thing she saw all week.

The hallway conversations beat the talks, as usual. Marcus ended up in a forty-minute discussion with an engineer from a payments company about idempotency keys, which is a problem we've been arguing about internally since March. He came back with a schema sketch on a napkin. We have since implemented it.

One thing we did not get: a clear answer on the migration question we went there to resolve. Nobody had run the exact configuration we're considering. That's worth knowing too, though it cost us three days and about six thousand dollars to learn.

Slides are in the shared drive. Ask Priya for the observability notes.
