**Eighteen Months, Forty Services, One Very Angry Database**

We split our billing monolith into microservices. It took eighteen months instead of the six we scoped, and about a third of what we built we later merged back together.

This talk is the postmortem I wish someone had given me in 2023.

I'll walk through the actual sequence: what we extracted first (payment webhooks, because they were already async), what we extracted second and shouldn't have (the customer record, which turned every read into three network hops), and the six weeks we spent unwinding that. There's a section on the shared Postgres instance nobody wanted to talk about. We kept it for fourteen months. Honestly, keeping it was the right call, and I'll explain why the dual-write pattern we tried first was worse.

Some numbers I'll share: p99 latency before and after, on-call pages per week, and how long a new engineer took to ship their first change (this one got worse before it got better).

Who this is for. Backend and platform engineers at companies with 20-200 people staring at a codebase everyone's afraid of. If you're at five people, please don't do this yet.

You'll leave with a list of the questions we didn't ask early enough.
