This is a stopslop project (writing rules enforcement), so let me write clean prose directly rather than routing through a skill meant for procedural docs.

Here's the post:

---

**Year in Review: Engineering, 2026**

We shipped less than we planned and more than we expected. The roadmap called for four major releases; we landed three, plus a rewrite of the ingestion pipeline that wasn't on anyone's calendar in January but became necessary after the March outage.

That outage is worth naming directly. A malformed batch from a partner feed took down search for six hours. The postmortem led to the schema validation layer we now run in front of every external write, and to a habit of writing postmortems for near-misses, not just outages.

The team grew from nine to fourteen. Onboarding got harder to do well at that size, so we wrote runbooks for the systems that used to live only in a few people's heads: deploys, on-call, the queue backpressure logic nobody could explain from memory.

Performance work paid off in a way we can measure. P95 latency on the API dropped from 340ms to 190ms, mostly from caching changes and one very stubborn N+1 query in the billing service.

We also killed things: two internal tools nobody used, a deploy process that took forty minutes, and a dependency on a library whose maintainer had gone quiet.

Next year: finish the migration off the old queue, get on-call load down for the smaller team members, and ship the analytics rework that's been half-built since August. None of it is glamorous. Most of the good work this year wasn't either.
