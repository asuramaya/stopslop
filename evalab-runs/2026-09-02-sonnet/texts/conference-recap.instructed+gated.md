Our platform team spent three days at KubeCon last month, and the trip paid for itself in the first afternoon.

The clearest signal came from the hallway track, not the sessions. We talked to four other teams running multi-tenant clusters at our scale, and three of them had hit the same etcd latency wall we hit in March. Two had solved it by splitting their control plane across regions before it became a customer-facing problem. We're now scoping the same split for Q4.

The talks reinforced what we already suspected: our alerting is too noisy and our on-call rotation is too long. A team from a mid-size fintech company walked through how they cut alert volume by 70% by tying every page to a customer-facing SLO instead of a raw metric threshold. We're stealing that approach directly. Priya is drafting the SLO list this week.

We also learned we're behind on policy-as-code. Most teams we spoke with have OPA or Kyverno enforcing pod security standards at admission time. We still do it with a linter in CI, which means bad configs can reach staging before anyone notices. That's now a backlog item for next sprint.

Not everything was useful. The keynotes leaned heavily on AI-assisted operations, and none of the three vendors we talked to could describe a production deployment beyond a pilot. We're not chasing that yet.

We're queuing one architecture change, starting one alerting rework, and closing one security gap before it bit us. Worth the flights.
