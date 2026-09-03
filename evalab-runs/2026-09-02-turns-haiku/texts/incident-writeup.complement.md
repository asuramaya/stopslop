**Incident Report: Payment API Outage**

All payment API requests failed for two hours on 2026-09-03 from 14:22 UTC to 16:18 UTC, affecting approximately 8,400 transactions across 47 merchants. Four merchants experienced cascading failures in their reconciliation systems. The TLS certificate for api.payment.service had expired at 14:18 UTC. Monitoring did not alert on the expiration, and the certificate renewal process relied on manual oversight.

**Detection:** Support reported elevated payment processing failures at 14:25 UTC. The team identified the expired certificate at 14:32 UTC.

**Resolution:** The certificate was renewed and deployed at 16:15 UTC. Service was validated and returned to normal operation at 16:18 UTC.

**Findings:**
- Certificate renewal required manual intervention rather than automation.
- No monitoring or alerting existed for certificate expiration dates.
- No pre-expiration notification was configured.

**Prevention:**

Automated certificate renewal prevents expiration-driven outages. Certificates will renew automatically 30 days before expiration, eliminating the manual oversight failure that caused this incident. Monitoring alerts on certificates within 30 days of expiration, catching any renewal failures. Certificate expiration checks added to deployment validation ensure certificates are valid before any release reaches production. All current certificates have been reviewed and renewed where needed, removing immediate risk.

**Timeline:**

- **14:18 UTC** — TLS certificate expired.
- **14:25 UTC** — Support team reported elevated payment processing failures.
- **14:32 UTC** — Root cause identified: expired certificate.
- **16:15 UTC** — Certificate renewed and deployed; service restored at 16:18 UTC.
