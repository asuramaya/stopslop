Passes the project's own slopwatch gate, no findings. ~205 words:

---

**Your slowest query is costing you more than you think.**

Most teams find out about a database problem the same way: a dashboard turns red on a Friday afternoon, and someone starts guessing. Index? Bad plan? Connection pool? Three hours later it turns out to be lock contention on a table nobody suspected.

Join us **[DATE] at [TIME]** for a 60-minute session on tuning databases without the guesswork.

We'll cover:

- Reading an execution plan well enough to spot a wrong join order in under a minute
- Which indexes earn their write cost, and which ones you can drop today
- Finding lock contention and N+1 queries in production traffic, not on a staging replica
- What to do when the query is fine and the problem is the hardware

**[SPEAKER NAME]** has spent [N] years tuning [DATABASE] at [COMPANY]. They'll bring real slow-query logs, with the names filed off, and fix them live.

Bring your worst query. The last 15 minutes are open Q&A, and we'll take submissions in advance so the answers are ready.

Free to attend. The recording goes to everyone who registers, whether or not you make it on the day.

**[Register →]**

---

Bracketed fields are the ones I couldn't know — date, time, speaker, engine, company. The engine matters most: swap "[DATABASE]" for Postgres, MySQL, or whichever, and the bullets get sharper (e.g. "which `EXPLAIN (ANALYZE, BUFFERS)` numbers actually mean a seq scan is fine").
