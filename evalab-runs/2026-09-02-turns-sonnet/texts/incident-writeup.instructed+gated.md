A payment API outage on September 3, 2026 blocked checkout, refund, and webhook traffic for 2 hours 4 minutes, failing an estimated 41,000 requests and delaying $187,000 in transactions, $12,000 of which clients never retried. An expired TLS certificate caused it.

Timeline:

14:12 UTC — TLS certificate expires; all payment API requests begin failing.
14:15 UTC — Datadog pages on-call after error rates cross 50%.
14:22 UTC — On-call engineer confirms the expired certificate as root cause.
16:16 UTC — Manual certificate deployed to the load balancer fleet; service restored.

The certificate was issued for one year and set to auto-renew 30 days before expiry. The renewal job depended on a DNS-01 challenge record that a prior infrastructure change had removed, and it failed silently three times over the preceding month.

No alert fired during that month because monitoring checked certificate presence, not expiry date or renewal success.

A certificate-expiry alert firing 14 days before expiry, independent of the renewal job, will surface the failure even if the renewal job stays broken. A renewal-success check runs after each renewal attempt and alerts on failure — the current check only confirms a certificate is present, which is why three failed renewals went unnoticed. We restore the DNS-01 challenge record this week. DNS records required for certificate renewal go into infrastructure-as-code review, so a future change cannot remove one without a reviewer seeing the dependency.
