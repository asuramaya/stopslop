**Your slowest query is not a mystery. Come find it.**

Most database slowdowns trace back to a handful of causes: an index the planner won't use, a join order that made sense at 10,000 rows and doesn't at 10 million, a connection pool sized by guesswork. This webinar walks through how to find which one you have.

We spend the first half on reading execution plans. Not the syntax, which you can look up, but the parts that actually predict trouble: row estimates that diverge from reality, sequential scans hiding under a nested loop, sorts that spill to disk. You'll see plans from real production incidents, including one where adding an index made things worse.

The second half covers what to do next. Index design and its write-side cost, when to denormalize, how to size a connection pool against your actual concurrency rather than a number from a blog post.

Examples use PostgreSQL and MySQL. The reasoning carries over to most relational engines.

Bring a slow query if you have one. We'll take audience submissions in the last twenty minutes and work through as many as time allows.

**Thursday, October 9, 1:00 pm ET. 90 minutes. Recording sent to everyone who registers.**
