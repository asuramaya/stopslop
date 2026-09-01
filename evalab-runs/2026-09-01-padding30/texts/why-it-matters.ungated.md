Passes the project's own slopwatch gate. Draft (~255 words):

---

## Nobody reads the logs until something burns

Three in the morning. Checkout is failing for maybe one in forty customers, and the dashboard is green.

That gap — between a system that looks fine and a system that is fine — is the whole argument for observability, and most teams only feel it during an incident, when the cost of learning is highest.

Monitoring answers questions you thought to ask in advance. You picked the metrics, set the thresholds, wired the pages. It works right up until the failure is something nobody predicted, which, for any service with more than a handful of moving parts, is most failures. A p99 latency graph will not tell you that the slow requests all come from one tenant whose account has 400,000 rows in a table you assumed held ten.

Observability is the ability to ask a new question of a running system without shipping new code to answer it. In practice that means traces that carry request context across service boundaries, structured events rich enough to slice by customer or region or build SHA, and logs someone can actually search.

The payoff is not shorter incidents, though incidents do get shorter. It is that engineers stop guessing. Debugging turns from an argument about whose service is at fault into a query, and the person running that query is often whoever shipped the code last week, not the one who has been here six years and remembers where the bodies are.

---

Two things you may want to swap: the "one in forty checkout failures" and the 400,000-row tenant are invented specifics — replace them with a real incident from your team and the section gets noticeably stronger.
