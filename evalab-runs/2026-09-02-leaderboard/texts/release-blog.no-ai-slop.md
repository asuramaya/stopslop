# Nimbus 2.0

Nimbus 2.0 is out today. It rewrites the request layer, and it breaks two things you probably use.

**Retries are per-request now.** In 1.x, setting `retries=5` on the client applied to every call, including the ones you wanted to fail fast. A dropped webhook delivery could hold a worker for 30 seconds. You now pass a retry policy to the individual call, and the client default is a single attempt.

**Pagination returns an iterator.** `client.users.list()` used to fetch every page before returning anything. A customer with 400,000 users got an out-of-memory crash, and we got the support ticket. The new version yields records as pages arrive.

Two more breaking changes. `NimbusLegacyAuth` is gone; use API keys or OAuth. And `timeout` now means total elapsed time rather than connect time, so `timeout=2`, which used to permit a 90-second read, raises after two seconds.

Every endpoint returns a dataclass generated from our OpenAPI spec, so `user.created_at` is a `datetime` and your editor knows what fields exist. No more dictionary lookups that fail in production because a key got renamed.

The 1.x branch gets security fixes until March 1, 2027. We wrote `nimbus-migrate` to handle the mechanical parts of the upgrade; on our own billing service it rewrote 90 of 104 call sites, and the remaining 14 were all custom retry logic that needed a human decision.

Install it with `pip install nimbus==2.0.0`. The migration guide lists every changed signature, and the changelog covers the smaller fixes.
