**Your queries are slow and nobody knows why**

Thursday, October 16, 2:00 PM ET — 60 minutes, live.

Most database slowdowns come from a short list of causes: a missing index, a query plan that flipped after the table grew, a connection pool sized by guesswork, or a lock held longer than anyone intended. This session walks through how to find which one you have.

We'll start with a Postgres instance carrying a deliberately bad schema and about 40 million rows. You'll see `EXPLAIN ANALYZE` output read line by line, including the parts people skip. From there we cover index selection (and when a second index makes writes worse), what to change when the planner picks a sequential scan over your index, and how to read wait events instead of guessing at them.

Bring a slow query. We're reserving the last 15 minutes for live diagnosis, and we'll work through as many as time allows. Paste yours in the registration form and it may be one we open.

Presented by Dana Okafor, who spent six years on database reliability at a payments company and has since tuned clusters for teams ranging from four engineers to four hundred.

Recording goes to everyone who registers, whether or not you attend.

[Register free]
