Platform Engineering Team Charter

The platform team exists to give product engineers a paved path from code to production, so they spend their time on features instead of infrastructure. We own the tools, environments, and standards that every service runs on: CI/CD pipelines, Kubernetes clusters, internal developer platform, and the golden-path templates teams start new projects from.

We measure success by deploy frequency, lead time for changes, and time to restore service after an incident. Engineering teams should be able to take an idea from a merged pull request to a running service in under fifteen minutes, without filing a ticket or waiting on us.

We build for the common case first. When three or more teams need the same capability, we build it once, into the platform, rather than let each team solve it separately. When a team's need is unusual, we give them the primitives to build it themselves rather than take on a one-off maintenance burden.

We support what we build. Every service we own has an on-call rotation, a runbook, and a defined SLO. If a platform component breaks, our team is paged first, not the teams depending on it.

We hold two standing commitments to the rest of engineering: no breaking change ships without a migration path and a two-week deprecation notice, and no platform outage lasts longer than the SLO we published for it.

This charter covers the CI/CD system, container orchestration, internal developer tooling, and shared infrastructure modules. It does not cover application-level code, product data pipelines, or team-specific business logic — those stay with the teams that own them.
