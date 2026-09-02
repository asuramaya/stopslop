# Vision

Two years from now, a new service at this company goes from empty repo to production traffic in under a week, and the engineer who builds it never files a ticket with us.

That is the target. Today the same work takes six to nine weeks, and most of it is not the service. Engineers hand-roll deploy pipelines, copy a Terraform module that someone wrote in 2023 and nobody owns, and wait on us to provision a database. We handle each request well. We handle far too many of them.

We will build the paved road so that the fast path and the correct path are the same path. Service scaffolding, deploy, observability wiring, secrets, and database provisioning all come from one toolchain that a product engineer drives without asking permission. Where a team needs something the road does not cover, they take the dirt path and keep ownership of it. We do not block that; we make the road good enough that few choose the dirt.

Success looks concrete. Median time from repo creation to first production deploy drops from 41 days to 5. Platform tickets per product engineer per quarter drop by half. Product teams spend at least 80% of their engineering hours on product code, measured by our own commit analysis rather than by survey.

This costs us roughly eight engineer-years over the two years, drawn from the infrastructure and developer-tools groups. During that stretch we will say no to custom infrastructure requests we would have taken on before, and some teams will feel that. We think the trade is worth making, and we would rather argue about it now than discover the disagreement in month fourteen.
