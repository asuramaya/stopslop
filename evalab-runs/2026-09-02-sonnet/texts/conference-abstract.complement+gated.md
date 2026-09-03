Moving Checkout Off the Monolith

Two years ago our checkout system was a single Rails app that took twelve minutes to deploy and failed as one unit whenever any part of it failed. This talk walks through the migration to microservices, how we split the codebase, what we got wrong the first time, and what actually changed in production.

We started by extracting the payment module, since it had the clearest boundary and the most on-call pages. That extraction took three months and taught us that a shared database is not a boundary. From there we cover service discovery, the switch from synchronous calls to an event queue, and the on-call rotation we rebuilt around service ownership instead of one team owning everything. Along the way, a distributed transaction bug corrupted order state for six hours, a retry storm took down our own API gateway, and it took six months to get tracing working well enough to debug a request across four services.

By the end, deploys take ninety seconds.

Attendees will leave with a checklist for deciding which parts of a monolith to split first, and which parts to leave alone.
