# Design note: signed cookies for session state

Recommend we put the session in a signed cookie and drop the server-side session table.

At 50,000 daily users, a session table earns its keep only if we need what it offers. We do not. Our sessions hold three fields: user id, role, and issue time. That payload fits well under 4 KB, so the browser can carry it.

Three points make the case.

First, we delete a database read from every authenticated request. Today each request pays for one lookup before any real work starts. That lookup is pure overhead. A signature check runs in microseconds on the app server and touches no network.

Second, the app becomes stateless. Any instance serves any request. Deploys, autoscale events, and instance failures no longer evict sessions. We also retire the Redis cluster that fronts the table.

Third, we remove an operational chore. Nobody prunes expired rows or watches the table grow.

We pay for this with revocation. Once the server signs a cookie, that cookie stays valid until it expires. If a user changes their password, or an admin bans an account, the old cookie still works. Every workaround claws back part of the win. A short expiry plus a refresh token shrinks the window to minutes. A revocation list restores a lookup, though a much cheaper one than today.

The proposal is a 15-minute access cookie plus a refresh token stored on the user row. If compliance later demands instant revocation, we add the list then, and we still keep most of the gain.
