# Why observability matters

At 2:14 on a Tuesday morning, checkout starts failing for about one customer in twenty. The dashboard is green. CPU is fine, memory is fine, the health check returns 200. Someone gets paged anyway, because support tickets are arriving faster than anyone can read them.

The gap between a system reporting itself healthy and a system actually working is where most on-call time goes. Monitoring answers questions you thought to ask in advance: is the disk full, is the queue backing up, did the error rate cross 2%. Those alerts catch the failures you have already seen once. They are silent on the ones you haven't.

Charity Majors, who co-founded Honeycomb, frames the distinction around unknown-unknowns: can you ask a new question of your production data without shipping new code to answer it? If diagnosing that 5% checkout failure means adding a log line, opening a PR, waiting for CI, and deploying, then the answer is no, and your debugging loop is measured in hours per hypothesis.

What changes with real instrumentation is the shape of the investigation. Instead of guessing which service is at fault and reading its logs, you filter traces to the failing requests and look at what they share. Sometimes it's one payment provider timing out. Sometimes it's every request carrying a specific feature flag. Sometimes it's a single bad host that the load balancer never removed.

None of this requires a rewrite. It requires that requests carry context, and that context survives long enough to query.
