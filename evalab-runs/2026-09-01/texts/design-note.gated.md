## Design note: signed cookies for session state

**Recommendation:** store session state in a cookie signed with HMAC-SHA256, not in a server-side session table.

At 50,000 daily users we are looking at roughly 2–5 million authenticated requests a day. A session table turns every one of those into a read against shared state. That read is cheap in isolation and expensive as a dependency: it needs a Redis or Postgres instance sized for peak, monitored, backed up, failed over, and kept close to every app server we run. It becomes the thing that has to be up for anyone to be logged in.

A signed cookie moves that work to the CPU. The server holds a secret, writes `user_id|issued_at|expires_at` plus a MAC into the cookie, and verifies the MAC on each request. Verification is a few microseconds and touches nothing outside the process. App servers become stateless, so deploys, autoscaling, and multi-region routing stop needing session affinity or replication. We delete a whole tier from the architecture.

Keep the payload down to an ID, an issue timestamp, an expiry, and nothing else. Cookies ride on every request, so a fat payload taxes upload bandwidth on slow connections. Set `Secure`, `HttpOnly`, `SameSite=Lax`, and a 14-day expiry.

**The drawback:** we lose immediate revocation. A stolen cookie stays valid until it expires, and "log out all devices" no longer works by deleting rows. The usual mitigations both claw back some state: bump a per-user `sessions_valid_after` timestamp that we check on sensitive routes, or keep a small deny-list of revoked tokens. Either way, revocation is the price, and we should decide we can pay it before committing.
