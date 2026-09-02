Your slowest query isn't a mystery. It's a missing index — or three.

Most teams tune databases by folklore. Someone bumps the connection pool, someone else adds an index they read about on Hacker News, and the p99 sits right where it was.

On [DATE], [SPEAKER] walks through how we took a checkout endpoint from 1.4 seconds to 90ms without touching a line of application code. Live, against a Postgres instance with 40 million rows in it. What we'll cover:

- Reading an `EXPLAIN ANALYZE` plan — what the numbers actually mean, and which line is lying to you
- Why your index isn't being used, and the four reasons that explain most cases
- How to size a connection pool by picking a number instead of doubling the old one
- When tuning stops paying and you should shard

Bring a slow query. We're taking submissions ahead of time and debugging a few of them on the call — no slides for that part, just plan output on screen. 45 minutes, then Q&A until the questions run out.

Everyone who registers gets the recording, so sign up even if the time is bad for you.

[Register →]
