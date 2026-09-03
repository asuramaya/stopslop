Platform Engineering Team Charter

The Platform Engineering team builds and operates the internal systems that other engineering teams depend on to ship: CI/CD, developer tooling, cloud infrastructure, and the internal services layer. Our customers are internal engineers, and our product is the speed and reliability of their path from commit to production.

We own the build and deploy pipelines, infrastructure provisioning, service scaffolding, observability tooling, and the on-call rotation for the systems underneath them. We do not own individual product features or team-specific business logic. That stays with the teams closest to the customer.

We measure success by deploy frequency, lead time for changes, time to restore service after an incident, and the number of engineering hours saved through tooling we build once and every team reuses.

When a request comes in, we ask whether solving it centrally saves more time across the company than each team solving it alone. If yes, it is ours. If not, we help the requesting team build it themselves and document the pattern. Teams can opt out of our tooling if they have a documented reason, but the default path must always be the easiest one. We treat every manual runbook step as a bug in our automation.

We respond to platform incidents within 15 minutes during business hours. We publish a changelog for every breaking change at least one week ahead of rollout. We review this charter every two quarters and revise it as the team's scope changes.
