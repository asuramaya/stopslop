Draft below is 196 words. It passes codewatch clean; slopwatch's only flag is `colon_reveal` on the literal `Subject:` header, which is an email field label rather than a rhetorical reveal.

**Subject line:** Your p99 doubled and the query plan didn't change

---

Every team hits the point where the obvious fixes stop working. You added the index. You bumped the instance size. The read replica took some load off, and three weeks later you're back where you started.

Join us Thursday, October 9 at 1:00 PM ET for a 60-minute working session on database performance tuning, hosted by [Name], who spent six years on the storage team at [Company].

We'll go through three production incidents end to end: a lock contention problem that looked like a network issue, a query that got slow only after the table crossed 40 million rows, and an index that made writes worse than the scan it replaced. For each one you see the metrics we started with, the wrong turns we took, and what actually fixed it.

Bring a slow query. We're saving the last 20 minutes for questions, and we'd rather spend them on yours than on hypotheticals.

Postgres and MySQL examples throughout. If you can read an EXPLAIN plan, you'll keep up.

The recording goes out to everyone who registers, so sign up even if the time doesn't work.

[Register]

---

Placeholders to fill: speaker name, company, date/time, register link. If the audience skews less technical than "reads EXPLAIN plans," tell me and I'll swap that qualifier and the incident details for something less specific.
