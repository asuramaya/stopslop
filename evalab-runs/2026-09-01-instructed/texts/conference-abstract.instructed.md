# From one deploy to forty: what our monolith migration actually cost

Two years ago our Rails monolith took 55 minutes to deploy and one bad migration could take down checkout. We now run 38 services. This talk is the honest account of how we got there, including the parts we would not repeat.

I will walk through the decomposition order we chose (billing first, auth last, and why the reverse would have been easier), the strangler-fig routing layer that let us move traffic service by service, and the six months we spent running dual writes against two databases because we underestimated how much of our domain logic lived in foreign keys.

The cost side gets equal time. Our p99 latency went up 40ms. On-call pages tripled in the first quarter before tooling caught up. We hired two people whose job is mostly service discovery and tracing. Deploy time is now 4 minutes, and a checkout outage no longer touches search, so the trade was worth it for us, at a scale most teams do not have.

You will leave with a decomposition checklist, the three tests we used to decide whether a boundary was real, and a clear sense of when staying monolithic is the correct answer.
