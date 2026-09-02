**Senior Backend Engineer — Payments Platform**
Remote (US) or Chicago · $190–230k + equity

We move about $4B a year for 900 small-business lenders. The ledger service that does it is Go, Postgres, and Kafka, and it was written back when we handled a tenth of that volume. It shows.

You'd own it. In the first year, specifically: split the monolithic ledger writer into per-tenant partitions, get p99 settlement latency under 200 ms, and kill the nightly reconciliation batch that pages someone twice a month.

What we're looking for:

- 6+ years on backend services, at least two of them somewhere money was on the line — payments, lending, brokerage, exchange, doesn't matter which
- Real Postgres depth. You've chased a lock contention problem at 2 a.m. and can explain what you found.
- Fluency in distributed failure modes: idempotency, why exactly-once delivery is mostly a story people tell, reconciliation as a design principle rather than a cleanup job
- Go, or the appetite to pick it up in a month. Strong Java, Rust, and C++ folks are welcome.

What we don't want: services split up for the sake of it, a Kubernetes hobbyist, or anyone itching to rewrite the whole thing in something newer.

Thirty-four engineers total, six on payments. We deploy around 20 times a day. On-call is one week in six and it's quiet most weeks — keeping it that way is half the reason this role exists.

Process: 45-minute call with the hiring manager, then a paid take-home or a live debugging session (your call), then a half-day onsite. Two weeks start to finish.

---

~260 words. Every number, stack detail, and process step is invented — swap in your real ones, since the specificity is what makes it not read like every other posting.
