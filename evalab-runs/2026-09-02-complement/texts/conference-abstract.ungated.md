**We Broke the Monolith. Twice.**

Splitting a monolith is mostly not a technical problem. We learned that the hard way — the first attempt died eighteen months in, with eleven services, four of which couldn't deploy without the other three, and an on-call rotation nobody would join.

This talk is about the second attempt, which worked. I'll walk through how we picked the first seam (billing, because it had the cleanest data boundary and the angriest customers), why we ran the old and new paths side by side for six weeks comparing outputs before cutting over, and the three occasions we decided a proposed service should stay in the monolith.

Some numbers: what the shared database actually cost us, how long the strangler-fig migration took end to end (twenty-two months), and the two pieces of infrastructure — request tracing and a per-service ownership registry — we built in month fourteen and should have built in month one.

You'll leave with a checklist for deciding whether a piece of your system deserves to be a service at all, and a realistic sense of the bill. Distributed systems make a few problems easier. They make many more problems harder.

---

205 words. The specifics — eleven services, billing as the first seam, twenty-two months — are placeholders shaped to fit; swap in your real ones. The abstract works because of them, so keep them concrete rather than softening to "a large migration."
