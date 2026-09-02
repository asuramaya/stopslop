**From One Deploy to Forty: What We Learned Breaking Up a Ten-Year-Old Monolith**

Our billing platform ran as a single Rails application for a decade. It worked. It also took 45 minutes to deploy, and a bad migration in the reporting code could take checkout down with it.

This talk covers the eighteen months we spent pulling it apart, including the parts that went badly. We started with the wrong seams: we split by team ownership instead of by data boundaries, and spent four months untangling two services that shared a customer table. The second attempt used database-level access patterns to find the real cut lines, which worked better.

You will see the strangler-fig setup we used to route traffic incrementally, the contract tests that caught breaking changes between services, and the observability we had to build before any of it was safe. I will also show the numbers: deploy time, incident count, and on-call load before and after, plus the infrastructure cost increase nobody warned us about.

Attendees running a monolith they suspect has outgrown its shape will leave with a method for finding service boundaries, a rough sense of the timeline, and several specific mistakes they can skip.

Intended for engineers and tech leads with production experience on a large codebase.
