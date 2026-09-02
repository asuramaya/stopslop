# You can't debug what you can't see

The checkout service started throwing 502s at 2:47 a.m. By 3:10 four engineers were awake, and all four were guessing. One blamed the database. One blamed a deploy from Tuesday. Someone restarted a pod because restarting a pod sometimes works, and this time it did, and nobody ever found out why.

That team didn't have a debugging problem. They had a visibility problem.

Most engineering orgs know they're supposed to care about observability, in the vague way you know you're supposed to floss. So they buy a tool, wire up a dashboard of CPU and memory graphs, and consider the box ticked. Then the next incident arrives with a shape nobody anticipated — a slow dependency three hops downstream, a retry storm, a single tenant sending malformed payloads — and the dashboards say everything is fine, because dashboards only answer questions you thought to ask in advance.

That's the real distinction. Monitoring tells you whether the conditions you predicted have occurred. Observability is whether you can ask a question you've never asked before and get an answer from data you already have, without shipping code.

The gap between those two things is where your incidents live. It's also where your on-call rotation burns out, where your postmortems fill with "we're not sure," and where a five-minute fix costs three hours of archaeology.

Closing that gap is mostly a design decision, not a purchasing one.
