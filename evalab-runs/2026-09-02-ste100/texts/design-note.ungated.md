## Design note: signed cookies for session state

**Proposal:** store the session in a signed cookie (HMAC-SHA256 over user ID, issue time, and a small set of claims) rather than a `sessions` table keyed by an opaque ID.

**Why.** At 50k daily users the argument is not throughput — a session table would handle that load on a laptop. The argument is operational surface. A server-side table is one more thing to provision, back up, monitor, fail over, and reason about during an incident. It puts a database read in front of every authenticated request, which means every request now depends on the session store's availability and latency, including requests that touch nothing else. A signed cookie removes that dependency: any process holding the signing key can verify a request with no I/O. New app instances need no warm-up and no sticky routing, and a regional outage degrades to "users re-authenticate" rather than "users see errors."

**Shape.** Keep the payload under a few hundred bytes; `HttpOnly`, `Secure`, `SameSite=Lax`. Short TTL (15 minutes) with a longer-lived refresh token, so stale claims self-correct. Signing keys live in the secret store and rotate on a schedule, with the previous key accepted during overlap.

**The drawback.** You give up instant revocation. Between issuance and expiry the cookie is valid, so a logout, a ban, or a password change does not immediately kill live sessions. The usual fix — a revocation list checked per request — reintroduces the server-side lookup this design was meant to avoid. A 15-minute TTL bounds the exposure without fully closing it, and that bound is the real cost of the choice.
