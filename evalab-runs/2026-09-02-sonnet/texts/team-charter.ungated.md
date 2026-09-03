## Platform Engineering Team Charter

**Mission**

The platform team builds and operates the shared infrastructure, tooling, and internal services that let product engineers ship reliably and fast. We treat internal engineers as our customers and their productivity as our success metric.

**Scope**

- CI/CD pipelines and deployment tooling
- Cloud infrastructure, provisioning, and cost management
- Observability: logging, metrics, tracing, alerting
- Developer environments and local tooling
- Service scaffolding, internal libraries, and paved-road templates
- On-call tooling and incident response infrastructure

**What we own vs. what we don't**

We own the platform layer — the systems teams build on top of. We do not own individual product services, business logic, or feature roadmaps. We set defaults and provide golden paths; teams can deviate when they have a good reason, but we're not in the business of mandating without support.

**How we work**

- We measure ourselves by developer experience: build times, deploy frequency, time-to-first-commit for new hires, incident recovery time.
- We prioritize self-service over gatekeeping. If a request keeps landing in our queue, we build a tool so it doesn't have to.
- We run a public roadmap and take requests through an open backlog, not side channels.
- We staff on-call for platform-critical systems and treat platform outages with the same severity as customer-facing outages.

**Success looks like**

Product teams spend their time on product work, not fighting infrastructure. Onboarding a new service or a new engineer takes hours, not weeks.
