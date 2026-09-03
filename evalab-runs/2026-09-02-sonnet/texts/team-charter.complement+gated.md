Platform Engineering Charter

The Platform Engineering team builds and operates the shared infrastructure other engineering teams depend on: CI/CD pipelines, deployment tooling, internal developer environments, observability, and the systems that provision compute, storage, and networking. Our customers are internal engineers, and our product is their ability to ship and operate software with confidence.

We treat platform work as product work. We gather requirements from the teams we serve, prioritize against measured pain points, and ship incrementally rather than in large rewrites. Engineers should be able to provision a new service, configure a pipeline, or roll back a deploy without filing a ticket. Where self-service isn't yet possible, we document the gap and treat it as a backlog item, not a permanent state.

We own the reliability of the systems we build. On-call for platform services sits with this team, not with the teams who use them. We set and publish SLOs for core services (build times, deploy latency, environment provisioning) and review them monthly.

We standardize where standardization reduces cost across the company, and we stay out of the way where it doesn't. We won't mandate a tool or pattern without a migration path and a clear reason tied to reliability, security, or maintenance cost.

Architecture decisions, roadmaps, and incident writeups are visible to every engineering team, not just requestors. Feedback from the teams we serve is a direct input to our roadmap, reviewed at each planning cycle.

We measure success by developer time saved, deployment frequency, and incident recovery time, not by the number of tools we ship.
