**Twelve Services Later: What We Got Wrong Splitting Our Monolith**

Two years ago our Rails monolith took 40 minutes to deploy and one bad migration could take down billing, search, and onboarding at once. We decided to split it. This talk covers what happened over the following eighteen months, including the four services we later merged back.

I'll show you the extraction order we chose and why it cost us six months. We pulled out the services that were easiest to isolate instead of the ones causing the most deploy contention, so our worst bottleneck stayed in the monolith until month fourteen. I'll walk through the database seam problem: three services sharing one Postgres instance because nobody wanted to own the customer table split.

You'll see our actual latency numbers before and after, including the endpoints that got slower. I'll cover the on-call load we added, the tracing setup we should have built first, and how we decided which boundaries were worth the network hop.

If your team is considering this move, you'll leave with a way to sequence extractions against your own deploy data, and a list of the signals that told us a service was drawn in the wrong place.

Aimed at engineers and leads who own a system big enough that deploys hurt.
