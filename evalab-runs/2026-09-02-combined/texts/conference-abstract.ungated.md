**Title: We Split the Monolith Into 40 Services. We'd Do It Again With 6.**

Everyone tells the same migration story: the strangler fig, the seams, the happy graph of small services. Ours went differently.

Three years ago our Rails app was a 400k-line checkout system with an 11-minute test suite and a deploy queue that backed up every Thursday. We decomposed it. Aggressively. By month eighteen we had forty services, a service mesh nobody fully understood, and a p99 that had gotten worse — because a single checkout now crossed nine network hops.

This talk is the honest version. I'll walk through the three extractions that paid for themselves (payments, search indexing, and the notification fan-out), the eleven that didn't, and how you can tell them apart *before* you write the migration ticket. We'll look at the actual latency traces, the on-call load before and after, and the year we spent building distributed-tracing tooling we would not have needed inside one process.

You'll leave with a decision test for whether a boundary is real, and a rough cost figure for what each new service actually charges you per year in operational overhead.

For teams considering the split, mid-split, or quietly regretting it.
