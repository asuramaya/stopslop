**From One Deploy to Forty: What We Learned Breaking Up a Nine-Year-Old Rails Monolith**

We spent eighteen months splitting a 400,000-line Rails application into 38 services. Along the way we shipped a distributed system that was slower than what we replaced, spent four months rebuilding our deploy pipeline, and rolled two services back into the monolith after they turned every checkout into a five-hop call chain.

This talk covers the decisions we got right and the ones we paid for. I'll show you how we picked the first three services to extract (billing, notifications, search indexing), why we chose the strangler-fig pattern over a rewrite, and the exact point where our observability stopped working. You'll see the dashboards we built when a single request started touching nine services, and the on-call runbook we rewrote three times.

I'll also cover what nobody warned us about: the org chart. Two teams ended up owning the same database table for seven months. Our staging environment cost more than production.

You'll leave with a checklist for deciding whether your monolith needs splitting at all, and a migration sequence you can adapt. Bring your architecture diagram if you have one.
