**Design note: signed cookies for session state**

I want us to drop the `sessions` table and put the session in a signed cookie instead.

The cookie carries a small payload: user ID, issue time, an expiry, and a version number for the auth epoch. We sign it with HMAC-SHA256 over a server-side key and reject anything that doesn't verify. Nothing secret goes in it, so signing is enough; we don't need encryption.

The case for it at our size is mostly about what we stop having to run. 50,000 daily users means roughly a few hundred session reads per second at peak, every one of them today a round trip to Postgres on the request path. Signature verification is microseconds of CPU in the app process. That removes a database dependency from every authenticated request, which also means auth keeps working during a database failover instead of logging everyone out. It removes the expired-session sweeper, the session table's write load, and one more thing to shard if we grow.

The drawback, and it's a real one: we lose instant revocation. A stolen cookie stays valid until it expires, because there's no server-side record to delete. Logging out on one device can't invalidate the others.

We can blunt this without giving up the win. Keep expiry short (30 minutes) with a refresh token that *is* checked against the database, so a revoked account dies within one refresh window. Bump the epoch version on password change to kill every outstanding cookie for that user at once.

Worth it. But we should agree on the refresh window before I build it.
