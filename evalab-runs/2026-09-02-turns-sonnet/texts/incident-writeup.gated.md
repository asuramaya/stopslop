Incident Report

Date: 2026-09-03 | Duration: 2 hours | Severity: High

Payment processing stopped for two hours. No transaction completed until the team restored service, and downstream customers saw errors on every attempt. The cause was an expired TLS certificate on the public endpoint, which broke the handshake and failed every request at connection time.

On-call traced the failure to the expired certificate on the load balancer, issued a new certificate, and deployed it. This restored TLS connectivity and ended the outage.

The certificate had no automated renewal process. No alerting system tracked its expiration date.

Timeline

- 09:00 — Certificate expires; TLS handshakes begin failing on the payment API endpoint.
- 09:03 — Monitoring detects the error-rate spike and pages on-call.
- 09:20 — On-call identifies the expired certificate on the load balancer as the root cause.
- 11:00 — New certificate deployed; TLS connectivity restored, traffic resumes.

What stops this from recurring

Manual certificate management caused this outage. Automation closes the gap.

The load balancer's certificate will renew through an ACME client (or equivalent managed-certificate service) on a fixed schedule, before expiry, so no person needs to remember the date. A monitoring check will query certificate expiry daily and page on-call at 30, 14, and 3 days out, so a human gets a window to intervene if renewal fails. Every production certificate will sit in a tracked list with an owner and expiry date, so none can exist outside the renewal and alerting system. The team will also audit all other production certificates now, so this outage does not repeat on a different endpoint next month.

Follow-up actions

1. Add automated certificate renewal.
2. Add alerting for certificates approaching expiration, with 30 days of advance warning.
3. Audit every production certificate for its expiration date.
