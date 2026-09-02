Subject: Atlas is moving to a new platform in Q1

We are moving the Atlas service onto our newer infrastructure between January 12 and March 6, 2027. Your account, data, and integrations move with it. You do not need to re-create anything.

Why we are doing this: the current platform runs on a database version that reaches end of support in June 2027, and the scheduling layer on top of it cannot handle jobs above roughly 40,000 rows without timing out. Both problems go away on the new stack.

What changes for you. API endpoints move from api.atlas.example.com/v1 to api.atlas.example.com/v2. The v1 endpoints keep working until September 30, 2027, so you have six months past the migration to update clients. Response shapes are unchanged except for the `job.status` field, which gains two values: `queued_retry` and `partial`. If your code branches on an exhaustive list of statuses, add handling for those before your account migrates.

What does not change: pricing, your existing API keys, webhook URLs, and the web console address.

Your migration window. We will email each account 14 days before its scheduled move, then again 24 hours before. Expect one read-only period of up to 45 minutes during the cutover, scheduled between 02:00 and 05:00 in your account's configured time zone. Writes queue during that period and apply afterward.

If the window we pick does not work, reply to the 14-day notice and we will reschedule you into any week through March 6.

Migration notes and a v1-to-v2 diff are at docs.atlas.example.com/v2-migration. Questions go to support@atlas.example.com.
