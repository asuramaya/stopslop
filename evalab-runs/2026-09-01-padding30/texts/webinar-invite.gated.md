Here's the copy (~200 words). It passes the repo's own `slopwatch` gate clean.

---

**Subject: Why your p99 comes back a week after you fix it**

Most database tuning is guesswork with extra steps. The dashboard goes red, someone adds an index, latency drops, everyone moves on. Three weeks later it's red again.

On **[DATE]** at **[TIME]**, **[SPEAKER]** is running a 60-minute session on the other way to do it: measure first, then change one thing.

We'll go through:

- Reading a query plan without glazing over, starting with what a nested loop over 400,000 rows actually costs you
- The four indexes that carry most workloads, and why the fifth one slows writes more than it speeds reads
- Connection pool sizing. The right number is smaller than you think, and here's the arithmetic
- A live teardown of two slow queries sent in by attendees

Bring a query. Send it ahead at **[LINK]** and we'll try to get to it on the call. **[SPEAKER]** has spent **[N]** years **[CONTEXT]**, mostly on Postgres and MySQL, and has opinions about ORMs.

No slides about digital transformation. The last 15 minutes are yours for questions.

**[REGISTER]**

Free to attend. The recording goes to everyone who registers, including the people who don't show up.

---

Two things to check before it ships: the bracketed fields are placeholders, and the specifics in the bullets (four indexes, 400,000 rows, Postgres/MySQL) are stand-ins I invented to keep the copy concrete — swap in whatever the speaker is actually covering, or the bullets will overpromise.
