**Summary**
A two-hour outage took the payment API fully offline, blocking all transactions fleet-wide. The cause was an expired TLS certificate on the edge load balancer, which triggered handshake failures on every incoming request.

**Root Cause**
The certificate's renewal was not automated, and the expiration date fell outside the window covered by manual tracking. No alert fired before expiry, so the team learned of the problem from client error reports rather than internal monitoring.

**Timeline**
- 09:58 — Certificate expired; TLS handshakes began failing.
- 10:04 — First customer reports of connection errors.
- 10:15 — On-call engineer confirmed expired cert as root cause.
- 11:58 — Certificate deployed and validated across all load balancer nodes; service restored.

**Impact**
All payment transactions failed during the outage window. No data was lost or corrupted; the failure occurred at the connection layer before requests reached application logic.

**Prevention**
- Automate certificate renewal (ACME/Let's Encrypt or equivalent) for all customer-facing endpoints, removing manual tracking from the process.
- Add expiry monitoring with alerts at 30, 14, and 3 days out, sent to the on-call channel.
- Add a synthetic check that validates certificate validity as part of uptime monitoring, so an expired cert triggers an internal alert before customers notice.
- Review all other certificates in use across the fleet to confirm none are approaching expiry under the same untracked process.
