**Sessions in a signed cookie**

At 50k daily users we expect maybe 200–400k session reads a day. Every one of them costs a round trip to the database, on the hot path of every request. That's a lot of infrastructure to hold a user ID and a timestamp.

The alternative: put the user ID, an issued-at time, and an expiry into a cookie, sign it with HMAC-SHA256, and verify on each request. Verification is a hash over a few hundred bytes — microseconds, no network, no connection pool. Auth is no longer a dependency. When the session store is a table, a slow query or a failover means nobody can log in. When it's a signature, the app stays up as long as it can read its own secret. A new instance needs no warm cache and no sticky routes.

The cost is real, and it's revocation. A signed cookie stays valid until it expires, full stop. If a user logs out on a stolen laptop, the old cookie still verifies. The same holds when an admin disables an account, or someone rotates a password after a scare. There's no row to delete.

Three things make that survivable. Keep expiry short — 30 minutes to a few hours — so the blast radius stays small. Include a `session_epoch` counter on the user record, bump it on logout-everywhere or password change, and check it on sensitive routes only. And keep the key rotatable, so a compromise doesn't mean permanent forgery.

If we later need instant revocation everywhere, we add a small denylist of revoked tokens — which is a cache, not a system of record.
