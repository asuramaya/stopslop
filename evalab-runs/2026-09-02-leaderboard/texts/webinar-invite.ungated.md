Placeholders in brackets — I don't have the date, speaker, or which database, so I picked Postgres for the concrete details. Swap freely.

---

**Your slowest query probably isn't the one you're watching**

Most teams find the same thing when they finally turn on query logging: the 4-second report everyone complains about runs twice a day. The 40-millisecond lookup underneath it runs eleven thousand times an hour. That one is eating the box.

On [DATE], [SPEAKER] shows you how to find it.

Ninety minutes, live, against a real Postgres instance with a deliberately awful schema. We'll read execution plans line by line — the part most tutorials skip — and work out why the planner ignored the index you just built. Then indexing strategy: composite column order, partial indexes, and the point where an index costs more in writes than it saves in reads.

Bring a slow query. The last half hour is open, and we'll put whatever you paste into the chat up on screen.

For backend and platform engineers who can write SQL but have never had to make it fast under load. No prior tuning experience assumed.

Recording goes to everyone who registers, whether or not you can make the time.

**[Register — DATE, TIME, 90 minutes]**

---

Roughly 185 words. If the webinar isn't hands-on or there's no live Q&A, tell me and I'll rework those two paragraphs — they're carrying most of the specificity.
