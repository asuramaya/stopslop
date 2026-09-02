247 words, and it passes the repo's own `slopwatch` ruleset clean. Bracketed placeholders are where your specifics go — you didn't name the service, the platform, or the quarter, so I left those as fill-ins and wrote the surrounding structure to be generic enough to survive whatever they are.

---

**Subject: Where [Service] is moving, and when**

We are moving [Service] to [New Platform] during [quarter]. Here is what that means for you.

Why: [current platform] caps us on [capacity / regions / support window], and we have hit that ceiling. The new platform lifts it, so we can spend our time adding to the service instead of working around the limit.

What stays the same: your account, your data, your plan and price, and the API endpoints your integrations already call. You do not need to rewrite anything.

What changes: the admin console moves to [url]. Single sign-on customers re-approve the connection once, at first login. If you use IP allowlists, add our new address range, which we publish four weeks before the move.

The schedule:

- [date] — new address range published, migration guide live
- [date] — opt-in early window for teams that want to go first
- [date] — everyone else moves, in batches by region
- [date] — old platform retired

Expect one maintenance window of up to two hours per batch. We will tell you your batch date at least 21 days ahead, and again 48 hours ahead.

If your team has a release, an audit, or anything else that makes a given week a bad one, write to [email] and we will move your batch. We would rather reschedule than surprise you.

Send questions to the same address. We will keep the migration guide current as the move goes on.

---

Two judgment calls worth flagging: I committed to concrete notice periods (four weeks, 21 days, 48 hours) because vague reassurance is what makes migration notices useless — swap in your real numbers or cut the sentence. And I included the reschedule offer, which is a real support commitment; drop that paragraph if you can't staff it.
